# TORMENT post-P7 native production validation: Stage 1R5

## Measured result

The client timed out after **240.016 seconds**. The server continued and returned
normally after **587.018371 seconds**, with HTTP 200 at the ASGI boundary.
The disconnected client received no status or response body. R3's formal
PRIVATE_NATIVE_QUERY = FAIL and R4's unresolved internal result remain unchanged.

The dominant stage is the current native **SQLite validation/read path**:
SQLite API calls consumed **581.451731 seconds (99.051710%)**.
Three all-root recovery/verification passes consumed **548.062745 seconds
(93.363815%)**, nested within that request. Root-profile verification ran
**471 times**, consuming **537.195110 seconds**. All three BGE encodes took
**0.058113 seconds**.

PRIVATE_QUERY_TIMEOUT_CLASS = SQLITE_READ_LATENCY.
SQLITE_MIGRATION_DIRECTLY_CAUSING_QUERY_TIMEOUT = YES uses this work order's
operational criterion: measured SQLite/native substrate operations directly
dominate this request. This identifies the current native validation/read path;
it does not establish an SQLite engine defect, corrupt database, index defect,
or a controlled performance comparison against the former backend.

R5 characterization is complete. Stage 1 remains held for architecture review.
No optimization or further production query was performed.

## Git state and frozen authority

~~~text
STARTING_HEAD = 6a492e23100558396e2a87b57b3ede1b6583bc8e
ORIGIN_MAIN_AT_START = 6a492e23100558396e2a87b57b3ede1b6583bc8e
HEAD_EQUALS_ORIGIN_MAIN_AT_START = YES
TRACKED_WORKTREE_AT_START = CLEAN
~~~

Preflight found no listener on port 8787. Existing untracked artifacts were
preserved. Final commit/push IDs and tracked-worktree verification are retained
in external publication_verification.json and the final delivery; the commit
containing this record identifies its source revision.

Startup and shutdown read-only receipts agree on:

- Selector generation 8, NATIVE_ACTIVE.
- Active core f21c730f-5222-4aa8-9a5f-1c1188456df3, ACTIVE_CORE, ever active.
- Profile digest 35ec54a0d5d3a2c87fedc855f8964615e4472876c3698488ba925a41a2ae717a.
- Immutable admission digest e4e510131cc341375485605bf1ead86aff684a1ca938e26fdbe221bbf0673ceb.
- Root completion v2, NATIVE_AGREEMENT, SQLite runtime **3.53.4**.
- Exact seven-field host profile from the selected core; no external admission
  descriptor or data-root override.

All project Python commands used Windows CMD and conda activate torment.
The service remained python -m torment_service. Launch retained
HF_HUB_OFFLINE=1, TORMENT_EMBED_PROVIDER=st, and TORMENT_EMBED_STRICT=1,
with canonical model/device defaults. The sole additional service setting was
TORMENT_DIAGNOSTIC_QUERY_TIMING=1, inside SETLOCAL.

Both cache checks matched all **29** R3 cache/lock file hashes, with no added,
removed, or changed files. Checks did not load a model. Frozen certified refusals
(35 memory and 23 motif), admission, selector, profile, schema, and authority
semantics were not changed or recertified.

Unchanged R4 record SHA-256:
19e056d84cff2e1d91253508c5d99684f035e84ab372c3aef10fea48e69225af.

Unchanged R3 record SHA-256:
46c99bb79674ae00dd813ac95e51f6d2078e34bb7139a091024025a74c830723.

## Instrumentation and safety

Existing facilities were insufficient: /embedder/check times an isolated probe;
native-vector tests include isolated benchmarks. Neither correlates the ordinary
production request through server completion.

The observability patch adds:

- An **off-by-default**, exact-value gate for POST /agent/query. Other routes
  have no collector. Without the gate set to 1, wrappers call originals directly.
- Request-local ContextVar state, monotonic perf_counter boundaries, inclusive
  and exclusive durations, counts, and at most eight samples per coarse stage.
- Three aggregate events: request start, endpoint completion, ASGI completion.
  No response header/body, query value/result, or authority decision is changed.
- Small decorators on the actual thinking, owner, root, BGE, query/vector,
  motif, filtering, and closure boundaries. No per-row/vector/scope or SQL-text logs.
- Gated SQLite connection/cursor subclasses at existing core/selector factories.
  Without a collector, sqlite3.connect receives unchanged arguments and returns
  native types. Explicit factories remain respected. Enabled subclasses time
  the same operations without adding SQL, transactions, pragmas, retries,
  connections, or concurrency.

SQLite timing covers the request-created connections through these factories.
Connections created before the request are not retrofitted. SQLite API time
includes execution, database/OS waits, row stepping, and row construction inside
that API; it is not an isolated SQLite VM CPU metric.

Targeted tests establish returned-object identity, unchanged exception propagation,
disabled silence, enabled output, validation and response parity, completion
evidence after failed send, bounded volume, identical SQLite statement traces,
results, transactions, factories and error behavior, plus the existing native REST
contract with diagnostics enabled.

| Validation | Result |
| --- | --- |
| New diagnostic tests | 6 passed in 6.79 s |
| Existing public backend, native owner, qualified query, native vector, root membership tests | 50 passed, 12 benchmark cases deselected, in 30.45 s |
| Final diagnostic and root membership rerun after last root counters | 27 passed in 8.22 s |
| Business AST comparison against starting HEAD, removing only timing hooks and restoring the connection helper name | PASS, all 17 modified existing modules |
| git diff --check | PASS |

There are **56 selected cases** excluding reruns. Existing files were
test_b5_a4r3_public_backend_selection.py,
test_b5_a3_production_native_resource_owner.py,
test_7g5e4e_native_query_read_model.py,
test_substrate_native_memory_vector_runtime.py, and
test_substrate_root_scope_membership.py. Scale and hot-path benchmarks were excluded.

The initial targeted attempt passed five tests but could not create the existing
pytest temp fixture due to Windows permissions. A new administration-owned temp
directory and disabled pytest cache resolved setup without cleanup. An initial
quoted -k command was rejected before collection; a corrected CMD script ran the
selection. Successful logs contain non-terminating Windows access-violation
diagnostics during import/filesystem operations; pytest completed with exit 0 and
all selected tests passed. Original logs are retained without claiming a host repair.

DIAGNOSTIC_INSTRUMENTATION_SEMANTIC_DELTA = NO.
No business statement, search/ranking rule, timeout, cache/memoization policy,
threading rule, or exception handling was changed. A post-measurement source
comment clarifies that the generic exception counter includes StopIteration;
it changes no execution or timing behavior.

## One query and server completion

Normal startup used service PID 36400. Pre-query health returned HTTP 200 in
0.047 s: native mode, strict canonical ST/BGE, dimension 384, cache size 0,
embedder_degraded=false.

The query client is byte-identical to R4's. It sent exactly one POST /agent/query
at 2026-09-10T07:17:22.022352+00:00 for workspace audit_smoke_v0_2,
agent smoke_runner, domain personal, with top_k=8, explain=true, and
continuity_debug=true. It retained the same 41-character smoke phrase, SHA-256
87c006c9b6f3609934e2cb92228df31747d4b1539c200dc3507949005e11ae8c.
No supplied vector or alternate search flag was added.

The original 240-second client timeout produced TimeoutError after 240.016 s,
no HTTP status, and zero response bytes. No second query was issued.
One post-timeout health request passed in 0.016 s during query execution.
An initial health-helper invocation failed argument parsing before issuing HTTP;
the corrected invocation issued only that health request.

The post-timeout observation bound was **900 seconds**, fixed before launch.
Server completion occurred about **347.002 seconds after the client timeout**,
inside that bound. Exactly one diagnostic request ID appears:
a180e109f7854b3eab5d2caf79ee93d8.

The endpoint recorded RETURNED; ASGI then recorded HTTP 200 and a returned
final-body send. Uvicorn can discard sends after disconnect: this establishes
server completion and response handling, **not delivery** to the timed-out
client or inspection of returned memory contents.

## Timing accounting

The denominator is the ASGI request span: **587.0183706999524 s**.
Rows are inclusive unless marked exclusive. Parent and child rows overlap;
the SQLite table is another view into the same request. **Do not add these rows.**

| Stage | Calls | Total elapsed (s) | % of measured request |
| --- | ---: | ---: | ---: |
| HTTP validation/dispatch before endpoint | 1 | 0.004896 | 0.000834% |
| Local thinking advisory | 1 | 0.001086 | 0.000185% |
| Native agent preparation (includes first owner recovery) | 1 | 182.805094 | 31.141290% |
| Native workspace view (includes second owner recovery) | 1 | 185.671602 | 31.629607% |
| Native read-context acquisition (includes third owner recovery) | 1 | 182.584236 | 31.103666% |
| Native owner recovery, all calls | 3 | 551.033825 | 93.869946% |
| Whole-root recovery and verification | 3 | 548.062745 | 93.363815% |
| Whole-root membership closure | 3 | 539.921854 | 91.976994% |
| Membership recovery | 468 | 537.858095 | 91.625428% |
| Root-profile verification | 471 | 537.195110 | 91.512487% |
| Record/completion agreement | 3 | 0.013036 | 0.002221% |
| Deployment/profile agreement | 3 | 2.969893 | 0.505929% |
| BGE encoding, seed and query text | 3 | 0.058113 | 0.009900% |
| Private search callback | 1 | 7.857086 | 1.338474% |
| Shared search callback (early return) | 1 | 0.000004 | 0.000001% |
| Qualified lane search | 1 | 5.626746 | 0.958530% |
| Vector snapshot acquisition | 1 | 0.005840 | 0.000995% |
| Vector snapshot construction | 1 | 0.005726 | 0.000975% |
| Vector search | 1 | 0.007217 | 0.001230% |
| Native candidate projection | 1 | 0.001218 | 0.000207% |
| Motif domain geometry | 2 | 22.319569 | 3.802193% |
| Active motif enrichment | 1 | 5.735260 | 0.977015% |
| Filtering | 1 | 0.011583 | 0.001973% |
| Native context closure | 1 | 0.001247 | 0.000212% |
| Fabric remainder: merge/ranking/continuity dispatch and other unspanned work (exclusive) | 1 | 0.004138 | 0.000705% |
| Serialization/ASGI response handling and bookkeeping after endpoint | 1 | 0.002487 | 0.000424% |

No lexical/full-text search was invoked. Text was encoded for vector search.
The shared-search callback ran once but returned before qualified shared vector
retrieval: **one private vector search/snapshot, zero shared vector
searches/snapshots**. Ordinary motif geometry reads were still invoked.
Timed Character assembly, native SRG continuity read, and process-overlay
replacement counts are zero.

Merge/ranking, continuity dispatch, and remaining Fabric work share its closest
truthful exclusive boundary (0.004138 s); production logic was not restructured.
HTTP authentication/body parsing/validation and dispatch share the prefix.
Serialization, response handling, and bookkeeping share the post-endpoint boundary.

All exclusive stage durations, including the HTTP remainder, sum to
**587.0183706999524 s (100%)** without overlap. Named stages excluding that outer
remainder cover **99.998815%**; the remainder is **0.006954 s**.
This is span accounting, not individual-line or individual-statement coverage.
Bookkeeping overhead is included, generally in parent self time.
No uninstrumented production control query was run.

## Whole-root validation and repeated work

WHOLE_ROOT_VALIDATION_CALL_COUNT and FULL_ROOT_VALIDATION_CALL_COUNT mean
the **three complete all-root recovery/verification passes** in
_recover_root_v2_workspace_runtime before selecting the workspace.
The combined boundary includes record/completion agreement, namespace/routing
checks, profile checks, membership closure, and disposition evidence.
It does not mean P6 admission or normalization was rerun.

| Root pass / caller | Owner recovery (s) | All-root recovery/verification (s) | Membership closure (s) |
| --- | ---: | ---: | ---: |
| 1. Agent preparation | 182.778780 | 181.716103 | 178.994302 |
| 2. Workspace view | 185.670856 | 184.718065 | 181.965826 |
| 3. Read context | 182.584188 | 181.628577 | 178.961725 |

The immutable record contains **154 scopes across 51 workspaces**:
76 private-agent and 78 shared-domain scopes. This aggregate came from existing
admission evidence, not a new census. Each pass rebuilds all runtime/routing
scopes and checks all memberships before selecting the requested workspace.

| Actual measured operation | Calls | Total elapsed (s) |
| --- | ---: | ---: |
| Native owner _recover_active_runtime | 3 | 551.033825 |
| Root _recover_root_v2_workspace_runtime | 3 | 548.062745 |
| root_membership_closure_digest | 3 | 539.921854 |
| _recover_memberships | 468 | 537.858095 |
| verify_root_profile_generation | 471 | 537.195110 |
| resolve_deployment_agreement | 3 | 2.969893 |
| _require_root_v2_record_agreement | 3 | 0.013036 |
| Immutable admission record decode/validation | 3 | 0.077933 |
| Disposition receipt/completion agreement | 3 | 0.000021 |
| verify_root_completion | 0 | 0 |
| _require_normalization_complete | 0 | 0 |

Each closure constructs RootScopeMembershipRuntime (one recovery), reads
cache_keys (one), then resolves 154 keys (154): **3 x (154 + 2) = 468**,
matching the measurement. Each recovery verifies the profile, plus one direct
profile verification per outer pass: **468 + 3 = 471**.

verify_root_profile_generation calls open_schema, then
current_root_profile_generation, which calls open_schema again. open_schema
enters _validate_schema; its successful path executes PRAGMA foreign_key_check
and PRAGMA integrity_check over the database. The **471 measured successful
profile verifications imply at least 942 schema validations** from this path
alone. This is a **code-derived lower bound**, not a directly recorded total.
Other schema gates exist. Individual integrity versus foreign-key-check costs
and exact total call counts were not separately instrumented. SQLite totals and
enclosing profile timings establish dominance without claiming that finer split.

REPEATED_EXPENSIVE_WORK_OBSERVED = YES.
Results are recomputed on each scope resolution; owner recovery reruns root
recovery before consulting a cached workspace view. The resolver explicitly
refreshes committed visibility to avoid stale active memberships after retirement.
Code establishes this behavior, but does not prove that the exact repeated
whole-database checking frequency is necessary under the frozen contract.

REPETITION_REQUIRED_BY_FROZEN_SEMANTICS = UNESTABLISHED.
Required authority verification and the necessity of every repeated expensive
check remain an architecture-review distinction. Nothing was removed or reused.

## SQLite timing

| SQLite API boundary | Calls | Total elapsed (s) | % of request |
| --- | ---: | ---: | ---: |
| sqlite.connect | 34 | 0.010603 | 0.001806% |
| sqlite.execute | 26143 | 579.323731 | 98.689200% |
| sqlite.fetch | 244423 | 2.087835 | 0.355668% |
| sqlite.close | 31 | 0.029563 | 0.005036% |
| **Total (non-overlapping SQLite leaf spans)** | | **581.451731** | **99.051710%** |

The **26,143 execute calls** include SELECTs and PRAGMAs. Significant SQL was
timed in aggregate without logging statement text. Qualified native core
connection acquisition was **10 calls, 5.665047 s**, including schema/qualification;
raw SQLite connection creation was **34 calls, 0.010603 s**.
Request-local close counts are not process-lifetime ownership accounting.

Execute/connect/close exception exits were **zero**, as were observed SQLite
BUSY/LOCKED error codes. The fetch exception-exit counter is **11,334** and
includes normal cursor StopIteration; it is not a SQLite failure count.
Fetch exception types and successful internal busy-handler waits were not
independently recorded.

SQLITE_DOMINANT_LATENCY_SOURCE = YES: measured SQLite API time alone accounts
for 99.051710%. Execution dominates fetching/materialization. The nested
471 profile verifications locate most of this cost.
No EXPLAIN, schema/index change, SQL rewrite, or SQLite setting repair was performed.

## BGE timing

Model initialization and its dimension probe finished during startup, before
query timing. The real canonical BAAI/bge-small-en-v1.5 model remained on CPU,
dimension 384, without fallback or replacement.

| BGE call | Parent stage | Start since request (s) | End since request (s) | Encode duration (s) |
| ---: | --- | ---: | ---: | ---: |
| 1 | native.kernel_initialization | 182.791653 | 182.813134 | 0.021481 |
| 2 | query.embedding | 551.069178 | 551.087427 | 0.018249 |
| 3 | vector.text_encode_entry | 564.439470 | 564.457854 | 0.018384 |

The first encode initializes the existing agent's in-process kernel from its
seed. The second is Fabric's query embedding; the third is the normal native
vector lane's query-text encode. Both query-text encodes total **0.036633 s**.
The direct Fabric embedding boundary including overhead is **0.018261 s**.
All three actual BGE encodes total **0.058113 s (0.009900%)**.
Encoding frequency, model settings, and cache policy were unchanged.

## Shutdown, evidence, and no repair

One Ctrl+C initiated normal Uvicorn shutdown. The log records application shutdown
complete and finished server process. Answering N to the CMD terminate-batch
prompt let the launcher preserve exit code **0**. The process and port-8787
listener were absent afterward. Read-only authority and cache checks passed.

External evidence:
C:\TORMENT\TORMENT_administration\post-p7-stage-1r5-20260910

The evidence_manifest.json hashes preflight, safety/test logs, AST verification,
launcher/profile proof, health/client receipts, raw timing events/summary,
process observations, post-timeout bound, post-shutdown authority/scale,
cache checks, and shutdown receipt. publication_verification.json separately
binds final Git IDs and this record's hash. Fixture directories are test data.

No optimization, caching/memoization, skipped/moved verification, index/schema
change, SQL rewrite, timeout increase, model/certificate/cache repair, authority
change, durable memory mutation, or separate shared/Character/trajectory query
was performed. No Stage-1 continuation or restart-persistence campaign occurred.

## Required return

Final Git IDs are supplied by publication verification and the final response.

~~~text
STARTING_HEAD = 6a492e23100558396e2a87b57b3ede1b6583bc8e
EXISTING_TIMING_INSTRUMENTATION_SUFFICIENT = NO
DIAGNOSTIC_INSTRUMENTATION_ADDED = YES
DIAGNOSTIC_INSTRUMENTATION_DEFAULT_OFF = YES
DIAGNOSTIC_INSTRUMENTATION_SEMANTIC_DELTA = NO
FOCUSED_TESTS = PASS (56 selected cases; final targeted/membership rerun: 27 passed)
R5_STARTUP = PASS
NATIVE_OWNER_RECOGNITION = PASS
SELECTOR_CORE_AGREEMENT = PASS
LEGACY_PUBLIC_FALLBACK_OBSERVED = NO
CLIENT_RESULT = TIMEOUT
CLIENT_ELAPSED = 240.016 seconds
SERVER_INTERNAL_RESULT = RETURNED_NORMALLY; HTTP_200_AT_ASGI_BOUNDARY_AFTER_CLIENT_DISCONNECT
SERVER_TOTAL_QUERY_DURATION = 587.018371 seconds
ROOT_AUTHORITY_RECOVERY_CALL_COUNT = 3
FULL_ROOT_VALIDATION_CALL_COUNT = 3
WHOLE_ROOT_VALIDATION_IN_QUERY_PATH = YES
WHOLE_ROOT_VALIDATION_CALL_COUNT = 3
WHOLE_ROOT_VALIDATION_TOTAL_DURATION = 548.062745 seconds (combined all-root recovery/verification)
QUERY_EMBEDDING_INVOKED = YES
BGE_ENCODING_CALL_COUNT = 3
QUERY_EMBEDDING_DURATION = 0.036633 seconds (two query-text encodes; excludes agent-seed encode)
SQLITE_MEASURED_TOTAL_DURATION = 581.451731 seconds
SQLITE_DOMINANT_LATENCY_SOURCE = YES
REPEATED_EXPENSIVE_WORK_OBSERVED = YES
REPETITION_REQUIRED_BY_FROZEN_SEMANTICS = UNESTABLISHED
PRIVATE_QUERY_DOMINANT_STAGE = SQLITE_API_EXECUTION_AND_FETCH_IN_NATIVE_VALIDATION_READ_PATH
PRIVATE_QUERY_DOMINANT_STAGE_PERCENT = 99.051710%
PRIVATE_QUERY_TIMEOUT_CLASS = SQLITE_READ_LATENCY
SQLITE_MIGRATION_DIRECTLY_CAUSING_QUERY_TIMEOUT = YES (measured current native SQLite validation/read path)
MEASURED_STAGE_TIME_ACCOUNTING_COVERAGE = 99.998815%
NORMAL_SHUTDOWN = PASS
POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_1R5 = PASS (characterization complete; client query still timed out)
POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_1 = HELD_FOR_REVIEW
SQLITE_MIGRATION_FULLY_VALIDATED = NO
NEXT_AUTHORIZATION_BOUNDARY = POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_1R5_REVIEW
~~~

STOP at POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_1R5_REVIEW.
