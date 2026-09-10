# TORMENT post-P7 native production validation: Stage 1R7

## Result and qualification limit

R7's bounded production read-only observations passed. The shared-enabled
ordinary query returned **HTTP 200 in 28.875 seconds** and exercised an actual
qualified shared vector search and snapshot. Three private controls also
returned HTTP 200 with valid result shapes and native namespace witnesses.
Production agent, workspace, and namespace isolation checks passed.

**All 78 existing admitted shared lanes contain zero memory aliases.**
The shared result is therefore a successful **empty shared-lane** observation.
It establishes normal routing, encoding, snapshot construction, and empty
retrieval, not ranking or projection over a populated shared corpus. No shared
memory was fabricated. The ordinary endpoint also searches the requesting
agent's private lane; its six returned private hits are expected.

POST_P7_NATIVE_PRODUCTION_READ_PARITY = PASS is limited to this existing corpus
and these bounded observations. Nonempty shared ranking remains unexercised.
Stage 1 overall remains HELD_FOR_REVIEW. No write/restart slice was started.

## Git and unchanged implementation

~~~text
STARTING_HEAD = 4fa3101d1892646f360b66c5976f3e448e2d4716
ORIGIN_MAIN_AT_START = 4fa3101d1892646f360b66c5976f3e448e2d4716
HEAD_EQUALS_ORIGIN_MAIN_AT_START = YES
TRACKED_WORKTREE_AT_START = CLEAN
BRANCH = main
PORT_8787_LISTENERS_AT_START = 0
~~~

This is an evidence-only repository change. No production source, tests,
instrumentation, schema, SQL, SQLite settings, timeout, model configuration,
verification frequency, or owner-recovery count changed. Existing untracked
artifacts were preserved. P1-P7 and R6 were not reopened or modified.

The R6 result record remains byte-identical, SHA-256:
**e64c07011e3ae9c3009bbc914d34cc95a77d6eddb851a035598d4fd5e49db0d6**.
R6's private-query qualification and amplification correction are retained.
No new regression suite was necessary for this documentation-only change;
R7 verification consists of the actual service observations, native witnesses,
existing diagnostics, and final evidence/Git checks.

Final literal Git IDs and this record's hash are recorded in external
publication_verification.json and the final response. The containing commit
identifies this record's revision without a self-referential embedded hash.

## Startup and authority

All project Python used Windows CMD with conda activate torment:
C:\Users\Notandi\miniconda3\envs\torment\python.exe, SQLite **3.53.4**.
The service ran normally as python -m torment_service, PID **51004**.
Startup completed and /health returned HTTP 200 in **0.015 seconds**.

The established process-local SETLOCAL configuration was retained:
TORMENT_DEPLOYMENT_PROFILE_JSON with the exact recovered seven fields,
TORMENT_EMBED_PROVIDER=st, TORMENT_EMBED_STRICT=1,
TORMENT_DIAGNOSTIC_QUERY_TIMING=1, and HF_HUB_OFFLINE=1.
No external admission descriptor or data-root override was used. Existing
diagnostics remained unchanged and default OFF outside this launcher.

Prelaunch and post-shutdown read-only authority receipts agree on:

- Selector generation **8**, NATIVE_ACTIVE.
- Active core **f21c730f-5222-4aa8-9a5f-1c1188456df3**, ACTIVE_CORE,
  ever_active=true.
- Profile digest
  **35ec54a0d5d3a2c87fedc855f8964615e4472876c3698488ba925a41a2ae717a**.
- Immutable root admission digest
  **e4e510131cc341375485605bf1ead86aff684a1ca938e26fdbe221bbf0673ceb**.
- Root completion witness v2 and NATIVE_AGREEMENT.

Health identified native public mode, strict canonical ST/BGE,
dimension 384, embedder_degraded=false. Startup and all queries used the
native owner. No legacy public fallback or maintenance-only posture appeared.

## Existing scopes and ordinary shared routing

The primary workspace, abbreviated H below, is:

~~~text
hivemind-natural-n5-v2-n5-20260825T201516Z-19a8097e25
~~~

Its existing admitted private agents include contrarian and empiricist, each
with eight current native memory aliases. Its admitted shared domain is
research. The shared memory source namespace is
**33aa18c5-f04b-4493-a393-3bf32d1d34a2**, semantic scope
**10134d43-116f-4c13-b37f-2847cb970d2a**, and motif domain research.

The other workspace is the R6 scope, audit_smoke_v0_2 / smoke_runner, with
five current private memory aliases and the admitted shared domain personal.
The selected private plans all retain motif_domain_id=None.

Scope selection first read the existing immutable admission record. Narrow
mode=ro alias/revision metadata observations then identified usable private
controls and established that every admitted shared lane has zero memory
aliases. This did not perform a new migration disposition or create any scope.

The ordinary [QueryReq](C:/TORMENT/TORMENT_repo/TORMENT-fabric_v2/torment_fabric/torment_service/app.py:467)
has agent/workspace/domain inputs, but no shared-only switch or lexical mode.
[Fabric.query](C:/TORMENT/TORMENT_repo/TORMENT-fabric_v2/torment_fabric/torment_service/fabric.py:4738)
merges the requesting agent's private results with enabled admitted shared
lanes. The existing thinking advisory enables relational retrieval for the
shared request's ordinary collaborative/memory wording. No memory-plan
override, manual vector, extra route, or provider setting was supplied.

The shared query text was:

> What have we previously agreed about our shared research?

Its SHA-256 is
**5a04d278aec630942d8da1335309c3b01a470f359df6d7368067efabc6726a18**.
The three private controls used R6's identical smoke text, SHA-256
**87c006c9b6f3609934e2cb92228df31747d4b1539c200dc3507949005e11ae8c**.

Every request used top_k=8, explain=true, continuity_debug=true, default
peek_bridges=false, and the unchanged **240-second** client timeout.
Exactly four POST /agent/query requests were sent; none was replayed.

## Production observations

| Observation | Workspace / agent / domain | HTTP | Client seconds | Server seconds | Private / shared vector searches | Private / shared returned hits |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Shared primary | H / contrarian / research | 200 | **28.875** | 28.858408 | 1 / 1 | 6 / 0 |
| Same-agent private control | H / contrarian / research | 200 | 27.515 | 27.515758 | 1 / 0 | 6 / 0 |
| Other-agent private control | H / empiricist / research | 200 | 27.266 | 27.249402 | 1 / 0 | 6 / 0 |
| Other-workspace private control | audit_smoke_v0_2 / smoke_runner / personal | 200 | 27.813 | 27.800304 | 1 / 0 | 5 / 0 |

All four result shapes passed: required keys, result-list and qualified-hit
shape, top_k limit, finite scores, zero authority-guard rejection, matching
excluded/filter_excluded aliases, and empty bridge-peek domains.
All completed normally at both the endpoint and ASGI boundaries; client
receipts independently confirm delivery.

The shared request produced two qualified lane-search samples, whose parents
were query.private_search and query.shared_search respectively. Existing
diagnostics measured two vector searches and two successful snapshot builds.
The shared search was not merely an early-return callback. Its domain_used
was exactly [research], the sole admitted shared domain in H.

[Native vector search](C:/TORMENT/TORMENT_repo/TORMENT-fabric_v2/torment_fabric/torment_service/substrate/native_memory_vector_runtime.py:336)
distinguishes an unavailable snapshot, which refuses, from a successfully
constructed empty snapshot, which returns no hits. R7 exercised the latter
for shared retrieval. This is SHARED_VECTOR_SEARCH = PASS for the existing
empty lane, without claiming a populated-corpus vector ranking test.

The initial external evidence helper misread the optional public motif-summary
shape as a domain-to-list map. After retaining the successful response shape
and all six native hit witnesses, it encountered the optional null
dominant_thread value and exited with TypeError. This was a client-side
post-response parser error, not a service failure. The original helper and
receipt are retained. The parser was corrected to read motifs.active, and
verify_saved_observation.py independently verified the already-recorded
receipt against the exact native aliases/current revisions. No query replay
or service instrumentation change occurred.

## Production isolation evidence

For all **23 returned-hit observations**, the client retained only authority
metadata, native identifiers, field names, and content hashes. It verified:

- workspace_id equals the requested workspace.
- Each private hit's agent_id equals the requesting agent.
- Any shared hit must belong to domain_used and an admitted shared scope;
  observed shared hits were zero, consistent with the empty shared corpus.
- The returned EID resolves once in the exact admitted source namespace.
- Its current native object/revision and effective semantic scope agree
  with that namespace's admitted binding.
- The current revision passes native semantic-lineage admission.
- The returned summary hash matches the native payload's summary/text
  projection. Raw memory text was neither printed nor retained.

The same private query against contrarian and empiricist returned local EIDs
**3, 4, 5, 6, 7, 8** on both sides, but every native object and source namespace
was different. Returned native-object sets were disjoint.

The same query against contrarian and the R6 workspace had overlapping local
EIDs **3, 4, 5**, again with distinct namespaces and disjoint native objects.
For example:

| Returned EID 4 | Native source namespace | Native object |
| --- | --- | --- |
| H / contrarian | 785e8621-a664-4496-8212-7c46233dc609 | d22db263-f207-4274-9add-d7d808393d65 |
| H / empiricist | b0f2add8-90fe-43cb-9c57-e1da5c9a0c30 | 4d2999a0-c907-4ec7-b9d5-fc36ff263e47 |
| audit_smoke_v0_2 / smoke_runner | bc5ba3ef-36f4-4aa0-9516-e46c1c0a6496 | ac04955a-b443-4824-aca6-cd0cfa237e83 |

These are actual production responses and native witnesses, not disposable
test results. They establish the requested bounded isolation observation.
They are not an exhaustive cross-product of every workspace, agent, and domain.
The empty shared corpus prevents a nonempty shared/private collision test.

PRIVATE_SHARED_SCOPE_ISOLATION_PRODUCTION = PASS within that stated scope.

## Lexical search classification

LEXICAL_SEARCH_PRODUCTION_SURFACE = NO for the active native production mode.
LEXICAL_TEXT_SEARCH = NOT_APPLICABLE.

The ordinary query request offers text-to-vector search; no lexical selector
exists in its schema or qualified native lane API. The internal
compat_query.search_text adapter also embeds text before vector retrieval.

A separate [archive-title sidecar route](C:/TORMENT/TORMENT_repo/TORMENT-fabric_v2/torment_fabric/torment_service/app.py:2022)
does exist in the application source. It delegates to fabric._get_sqlite_index
and uses [SQL LIKE over document titles](C:/TORMENT/TORMENT_repo/TORMENT-fabric_v2/torment_fabric/torment_service/sqlite_index.py:654).
It is a legacy sidecar compatibility surface, not an available native
production lexical lane: the active
[native public runtime rejects that fallthrough](C:/TORMENT/TORMENT_repo/TORMENT-fabric_v2/torment_fabric/torment_service/public_runtime.py:556).
The archive query route is cosine retrieval and likewise depends on the
legacy archive/sidecar path.

No lexical request, sidecar construction, index rebuild, or alternate internal
search invocation was performed. NO does not assert that lexical helpers or
legacy routes are absent from the repository.

## Model D and certified refusals

MODEL_D_PRESERVED = YES for the naturally observed routing.

The queried private root-P2 plans retain motif_domain_id=None. Each request's
domain_used was an existing admitted domain: research or personal.
The audit_smoke_v0_2 control naturally returned four active personal motifs:
motif_personal_0001 through motif_personal_0004. Read-only alias/current-state
lookups bound all four to:

~~~text
shared motif alias namespace = 31a6bf59-e3b8-41d9-874d-09076a94643c
shared semantic scope = bfba7bc1-71b7-4e55-9a72-d73f0cb692b9
current native motif payload domain = personal
private plan motif_domain_id = None
~~~

The unchanged shared
[list_runtime_motifs](C:/TORMENT/TORMENT_repo/TORMENT-fabric_v2/torment_fabric/torment_service/substrate/motif_runtime_reader.py:121)
uses strict_domain=True and refuses a domain mismatch. The private reader
uses the existing domain-filtered operation within its exact private namespace.
The ordinary query's shared active-motif/geometry reads retain that strict
shared path. No private motif-domain ID was synthesized and no extra query
was sent to force this observation.

The frozen P3 evidence still records **35 memory semantic-gap refusals** and
**23 motif member-semantic-gap refusals**. Returned native memory object IDs
were checked against the 35 certified objects; returned hit/active motif IDs
were checked using their workspace and lane qualifier against the 23 certified
motif identities. No match was observed. The unchanged core/WAL hashes also
exclude a durable successor or READY promotion during this service run.

CERTIFIED_REFUSAL_RUNTIME_LEAK_OBSERVED = NO is an observation of these results,
not a new P3 certification or corpus-wide runtime recensus.

## Models and diagnostic observations

Only local **BAAI/bge-small-en-v1.5** embedding was configured and observed:
strict ST provider, CPU, 384 dimensions, complete existing cache, offline
Hugging Face mode. No conversational/local generative model or external AI API
was configured or invoked by these query paths. The existing thinking advisory
uses deterministic local draft/rule logic.

There were **12 actual BGE encodes**, totaling **0.148917 seconds**:
4 for the shared primary, 2 for the already-prepared same-agent control,
3 for the other agent, and 3 for the other workspace. The first request for an
agent includes its existing in-process seed initialization; query text is
encoded by Fabric and each searched vector lane. Optional existing Character
context appeared in the H responses; it was read-only and is not a new
Character-continuity qualification.

Every request retained **three whole-root passes and 471 profile verifications**.
The shared primary measured 1,034 schema validations and 98 full FK/integrity
pairs; each private control measured 1,030 and 94 respectively. Existing R6
validation behavior remains intact. No request approached the 240-second
timeout or supplied evidence requiring a new optimization.

| Observation | SQLite API seconds | BGE seconds |
| --- | ---: | ---: |
| Shared primary | 26.347497 | 0.054354 |
| Same-agent private control | 25.047894 | 0.023332 |
| Other-agent private control | 24.897990 | 0.035134 |
| Other-workspace private control | 25.311401 | 0.036096 |

These are observational measurements, not benchmarks. Existing inclusive
stage spans overlap; SQLite leaf totals are another view of the same request.
All non-fetch diagnostic error counters and observed BUSY/LOCKED counts are
zero. The existing fetch exception counter includes normal StopIteration.
No new instrumentation was added.

## Shutdown and unchanged durable state

One Ctrl+C initiated normal Uvicorn shutdown. The log records application
shutdown complete and finished PID 51004. Answering N to CMD's terminate-batch
prompt let the launcher retain exit code **0**. The process and port-8787
listener were absent afterward.

Before startup and after shutdown, the production core was **82,747,392 bytes**
with identical SHA-256:
**eea6e07072e0cdad09ab2872203361c18adf19e044f452686249352aef84dc85**.
Its WAL was zero bytes at both observations, also with an identical hash.
The authority receipts agree, and all **29 model-cache/lock fingerprints**
remain unchanged with no additions or removals.

No memory write, reinforcement, Character mutation, trajectory write,
schema/data mutation, retirement, profile transition, or restart-persistence
campaign was performed.

## Evidence and required return

External evidence directory:
C:\TORMENT\TORMENT_administration\post-p7-stage-1r7-20260910

It retains the preflight, admitted-scope metadata, shared availability,
launcher/host proof, health receipt, four request intents and redacted
responses, original and corrected client helpers, saved-receipt verification,
12 existing timing events and summary, native isolation comparisons, Model D
motif witnesses, database/cache fingerprints, and shutdown observation.
evidence_manifest.json binds the top-level receipts/helpers and referenced
frozen refusal evidence. publication_verification.json separately binds the
final Git state, this record, and the manifest.

Final literal FINAL_HEAD and ORIGIN_MAIN are provided by publication
verification and the final response.

~~~text
STARTING_HEAD = 4fa3101d1892646f360b66c5976f3e448e2d4716
R7_STARTUP = PASS
NATIVE_OWNER_RECOGNITION = PASS
SELECTOR_CORE_AGREEMENT = PASS
LEGACY_PUBLIC_FALLBACK_OBSERVED = NO
MAINTENANCE_ONLY_POSTURE = NO
PRIVATE_NATIVE_QUERY = PASS (R6 retained; R7 controls also pass)
SHARED_NATIVE_QUERY = PASS (existing empty shared lane)
SHARED_QUERY_HTTP_STATUS = 200
SHARED_QUERY_CLIENT_ELAPSED = 28.875 s
SHARED_QUERY_RESULT_SHAPE = PASS
PRIVATE_SHARED_SCOPE_ISOLATION_PRODUCTION = PASS (bounded observations)
PRIVATE_VECTOR_SEARCH = PASS
SHARED_VECTOR_SEARCH = PASS (empty snapshot; nonempty ranking unexercised)
LEXICAL_SEARCH_PRODUCTION_SURFACE = NO (active native mode)
LEXICAL_TEXT_SEARCH = NOT_APPLICABLE
MODEL_D_PRESERVED = YES
CERTIFIED_REFUSAL_RUNTIME_LEAK_OBSERVED = NO
GENERATIVE_MODEL_INVOLVED = NO
GENERATIVE_MODEL_DETAILS = LOCAL_BGE_EMBEDDING_ONLY; 12_ENCODES; NO_GENERATIVE_PROVIDER
NORMAL_SHUTDOWN = PASS
POST_P7_NATIVE_PRODUCTION_READ_PARITY = PASS (existing corpus; stated empty-shared limit)
POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_1R7 = PASS
POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_1 = HELD_FOR_REVIEW
SQLITE_MIGRATION_FULLY_VALIDATED = NO
NEXT_AUTHORIZATION_BOUNDARY = POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_1_WRITE_RESTART_SLICE
~~~

Remaining Stage-1 work includes ordinary write/read-after-write, reinforcement,
Character continuity, native trajectory write, clean restart, post-restart
persistence, and trajectory authority reconstruction. These remain pending
authorization and were not begun.

STOP for review before POST_P7_NATIVE_PRODUCTION_VALIDATION_STAGE_1_WRITE_RESTART_SLICE.
