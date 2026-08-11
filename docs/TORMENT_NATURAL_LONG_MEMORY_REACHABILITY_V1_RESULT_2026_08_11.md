# TORMENT Natural Long Memory Reachability V1 Result

Preservation date: 2026-08-11

This note preserves the completed Experiment #4 result and records the adversarial-audit corrections without modifying the raw artifacts. The raw JSON artifacts remain immutable. This note is the corrected interpretive layer.

## Identity And Scope

Experiment: `NATURAL_LONG_MEMORY_REACHABILITY_V1`

Original subtype: `SCRIPTED_LIVED_USE_REACHABILITY_WITH_UNCHANGED_PRODUCTION_THRESHOLDS`

Frozen result scope: `SCRIPTED_PROVIDER_FREE_COMPRESSION_AND_DEEP_TEXT_RECORD_REACHABILITY`

Baseline:

```text
HEAD == origin/main == 6b1c3cc6ca53f074d66a146ae04532c7d703fc55
Subject: test(lived-use): preserve warmth feedback characterization
```

Configuration boundary: `NON_DEFAULT_COMPRESSION_ENABLED`

Production default: `TORMENT_COMPRESS_ENABLE=0`

Embedder: `ST_BGE_LIVED_USE_SEMANTIC`

Model: `BAAI/bge-small-en-v1.5`

Strict mode: enabled and empirically enforced

Provider: `NOT_INVOKED`

Transport boundary: `IN_PROCESS_ENDPOINT_EQUIVALENT_LIVED_USE_PATH`

Ingest summary builder: `examples.lived_use_chat.build_ingest_summary`

Do not describe this experiment as network/service-level execution. The completed run invoked real FastAPI endpoint functions with real Pydantic request models, but not through HTTP transport.

## Artifact Provenance

Harness:

```text
scripts/natural_long_memory_reachability_v1.py
```

Authoritative complete run:

```text
outputs/experiments/natural_long_memory_reachability_v1/20260811T123033Z/natural_long_memory_reachability_v1_result.json
```

Independent complete replication:

```text
outputs/experiments/natural_long_memory_reachability_v1/20260811T122627Z/natural_long_memory_reachability_v1_result.json
```

`20260811T122627Z` is not a failed run. It produced complete result JSON with identical final taxonomy, condition summaries, production compression triggers, first DeepMemory summaries/classes/scores, and `embedding_ref = null` behavior.

Freeze:

```text
INDEPENDENT_REPLICATION:
20260811T122627Z_IDENTICAL_TAXONOMY_AND_SUMMARIES
```

This demonstrates deterministic reproducibility of the same preregistered seeded pipeline. It is not independent statistical sampling.

Failed execution-provenance directories:

```text
20260811T122505Z
20260811T122548Z
```

`20260811T122505Z` failed with:

```text
ModuleNotFoundError: No module named 'examples'
```

It produced no result JSON, no memory nodes, no compression state, and no deep records.

`20260811T122548Z` failed while loading `BAAI/bge-small-en-v1.5` through HuggingFace/model fetch. It produced no result JSON, no memory nodes, no compression state, and no deep records.

Freeze:

```text
EMBEDDER_STRICT_MODE_ENFORCED:
DEMONSTRATED
```

The `20260811T122548Z` failure aborted rather than silently falling back to `HashEmbedding`.

The earlier TestClient/SQLite same-thread incident has no surviving run artifact.

Freeze:

```text
TESTCLIENT_SQLITE_SAME_THREAD_INCIDENT:
DOCUMENTED_IN_HARNESS_RATIONALE_ONLY_NO_SURVIVING_ARTIFACT
```

## Endpoint And Production Path

`DirectAppClient` invoked the real FastAPI endpoint functions using real Pydantic request models. Request validation was preserved.

The characterized memory/compression path included:

```text
app.query / app.ingest
Spine
TormentFabric.ingest
kernel.process
MemoryGraph
EventDetector
try_compress
CompressionScorer
CompressionRouter
CompressionExecutor
DeepMemoryStore
```

`AUTH_ENABLED=0` made `request=None` inert because `resolve_request_context` returns before dereferencing the request.

The transport adaptation changed threading/HTTP transport only for the characterized memory path.

Freeze:

```text
TRANSPORT_BOUNDARY:
IN_PROCESS_ENDPOINT_EQUIVALENT_LIVED_USE_PATH
```

## Step Accounting

Across all completed conditions, each successful scripted exchange corresponded to one ingest/kernel progression. Automatic production rows did not create additional canonical steps.

Checkpoints observed:

```text
exchange 50 -> step 50
exchange 100 -> step 100
exchange 150 -> step 150
exchange 200 -> step 200
exchange 250 -> step 250
```

Freeze:

```text
EXCHANGE_EQUALS_STEP:
DEMONSTRATED

MANUAL_STEP_ADVANCEMENT:
NOT_USED
```

## Condition A Default-Off

Condition A ran with `TORMENT_COMPRESS_ENABLE=0`.

Result:

```text
exchanges: 250
ingest outcomes:
  NEW_SOURCE_ROW: 13
  REINFORCEMENT_OF_EXISTING_ROW: 237
  OTHER: 0
compression events: 0
compression metadata: none
DeepMemory directory: absent
DeepMemory record: none
final graph entities: 15
```

The two additional graph rows are automatic production memories:

```text
seed_canon
identity_anchor
```

They are graph entities but not ordinary ingest outcomes. Do not add final graph rows to reinforcement outcome counts as if they share one accounting scope.

Freeze:

```text
DEFAULT_NEW_DEEP_FORMATION:
DISABLED_BY_DESIGN

DEFAULT_OFF_RUNTIME_CHECK_THROUGH_FIRST_FALLBACK_REGION:
DEMONSTRATED
```

The runtime check is subordinate to the structural configuration gate. This is not a compression failure.

## Compression Gate And First Triggers

Freeze:

```text
COMPRESSION_MIN_STEP_GATE:
100_CODE_TRACED_AND_OBSERVED
```

Production does not invoke `try_compress` below step 100. At step 100, `EventDetector` is initialized with `prev_in_corridor = None` and `prev_cycle_stage = None`, so the first detector call cannot produce `corridor_exit` or `cycle_stage_change`. Step 101 is the earliest structurally possible geometric trigger under this route.

Production `compression_log.jsonl` recorded:

```text
T1:
  step: 105
  trigger: corridor_exit
  candidates: 20
  compressed: 19
  exported_deep: 1

T2:
  step: 105
  trigger: corridor_exit
  candidates: 20
  compressed: 19
  exported_deep: 1

T3:
  step: 101
  trigger: cycle_stage_change
  candidates: 14
  compressed: 13
  exported_deep: 1
```

Freeze:

```text
FIRST_COMPRESSION_TRIGGER_T1:
corridor_exit @ 105

FIRST_COMPRESSION_TRIGGER_T2:
corridor_exit @ 105

FIRST_COMPRESSION_TRIGGER_T3:
cycle_stage_change @ 101

FIRST_COMPRESSION_TRIGGER_CLASS:
GEOMETRIC_NOT_FALLBACK

FALLBACK_PERIODIC_STEP_201_REQUIRED:
CONTRADICTED

STEP_201_CODE_TRACE_STATUS:
CORRECT_AS_A_NO_EARLIER_EVENT_FALLBACK_EXPECTATION
```

The experiment did not show that the step-201 trace was wrong. It showed that its no-earlier-geometric-event antecedent did not hold.

## First Compression Contents

The first compression event had the same structural pattern in T1/T2/T3:

```text
ordinary relational rows -> short_path
one automatic identity_anchor -> long_path
```

Counts:

```text
T1: 19 relational short_path, 1 identity_anchor long_path
T2: 19 relational short_path, 1 identity_anchor long_path
T3: 13 relational short_path, 1 identity_anchor long_path
```

Candidate-cap behavior:

```text
COMPRESS_MAX_CANDIDATES = 20
T1 left one otherwise eligible/scorable row untouched.
T2 left five otherwise eligible/scorable rows untouched.
```

The untouched sets match production state exactly.

## Identity Anchor Origin

Freeze:

```text
IDENTITY_ANCHOR_IS_AUTOMATIC_PRODUCTION_MEMORY:
YES

HARNESS_CREATED_OR_FORCED_IDENTITY_ANCHOR:
NO
```

The identity anchor is emitted by `TormentFabric._maybe_emit_identity_anchor` during ordinary ingest after motif accumulation.

Relevant default gates include:

```text
minimum motif agent-owned member count: 3
minimum gap between anchors for a motif: 50 steps
maximum examples in anchor summary: 2
```

Observed anchor birth:

```text
T1: step 3
T2: step 3
T3: step 4
Condition A: step 4
```

Observed anchor properties:

```text
type: identity_anchor
canon: false
half_life: 3650 days
strength before compression: 0.79
reinforcement_count: 0
```

The identity anchor exists even with compression disabled, as demonstrated in Condition A.

Observed automatic row classes across the experiment:

```text
AUTOMATIC_ROW_CLASSES_OBSERVED:
seed_canon, identity_anchor, drift_correction
```

`drift_correction` was observed in T2.

## Identity-Tier Routing

Freeze:

```text
FIRST_LONG_PATH_SOURCE_CLASS:
AUTOMATIC_IDENTITY_ANCHOR

FIRST_LONG_PATH_CAUSE:
IDENTITY_TIER_OVERRIDE
```

Retention tier is derived as `identity` because the anchor has `half_life >= 365`. The anchor's 3650-day half-life therefore creates `tier == identity`, and `CompressionRouter.route` returns `long_path` immediately for identity tier before ordinary age/score conditions are checked.

Observed first-deep anchor:

```text
compression_score: 0.4859
age: 97-102
```

It independently fails the ordinary long-path conditions:

```text
score >= 0.7: FAILED
age >= 500: FAILED
memory_class == archive: FAILED
echo tier and age >= 150: FAILED
```

Without the identity-tier override, it would not long-path. Do not call this `MATURE_HIGH_SCORE_RELATIONAL_MEMORY`.

## Ordinary Relational Long-Path

Freeze:

```text
ORDINARY_RELATIONAL_LONG_PATH_REACHABILITY:
NOT_DEMONSTRATED
```

No ordinary relational row long-pathed anywhere in T1/T2/T3.

Observed relational range:

```text
oldest relational age: approximately 100-104
best observed relational compression score: 0.5652
```

Ordinary score/age route requires:

```text
score >= 0.7
AND
age >= 500
```

Freeze:

```text
ORDINARY_RELATIONAL_LONG_PATH_STRUCTURALLY_UNREACHABLE_BELOW_STEP_500:
CODE_TRACED_AND_CONSISTENT_WITH_OBSERVATION
```

Do not say ordinary memories enter Deep Memory around exchange 100 or that exchange 101/105 is episodic maturity. At those steps, ordinary relational rows were short-path weakened in place.

## Reinforcement And Graph Growth

Observed accounting:

```text
Condition A:
  exchanges: 250
  ordinary new rows: 13
  reinforcements: 237
  final graph rows: 15 including 2 automatic rows

T1:
  exchanges: 105
  ordinary new rows: 20
  reinforcements: 85
  final graph rows: 22 including 2 automatic rows

T2:
  exchanges: 105
  ordinary new rows: 24
  reinforcements: 81
  final graph rows: 27 including 3 automatic rows

T3:
  exchanges: 101
  ordinary new rows: 13
  reinforcements: 88
  final graph rows: 15 including 2 automatic rows
```

Freeze:

```text
REINFORCEMENT_MATERIAL_TO_GRAPH_GROWTH:
DEMONSTRATED

REINFORCEMENT_MATERIAL_TO_FIRST_DEEP_REACHABILITY:
NOT_ISOLATED
```

Semantic reinforcement absorbed many scripted exchanges into relatively few graph rows. But the first deep source was an identity anchor with `reinforcement_count = 0`, and first compression was caused by kernel geometry rather than graph-count overflow. Do not infer first-deep timing from reinforcement rate.

## Trajectory Interpretation

Do not freeze the original broad labels:

```text
DISTINCT_EPISODE_REACHABILITY: DEMONSTRATED
RECURRING_TOPIC_REACHABILITY: DEMONSTRATED
MIXED_CHARACTER_REACHABILITY: DEMONSTRATED
```

Replace and rescope as:

```text
T1_REACHED_DEEP_TEXT_RECORD_VIA_IDENTITY_ANCHOR:
DEMONSTRATED

T2_REACHED_DEEP_TEXT_RECORD_VIA_IDENTITY_ANCHOR:
DEMONSTRATED

T3_REACHED_DEEP_TEXT_RECORD_VIA_IDENTITY_ANCHOR:
DEMONSTRATED

STYLE_INDEPENDENT_REACHABILITY:
NOT_ISOLATED

TRAJECTORY_DEPENDENCE_OF_FIRST_DEEP_REACHABILITY:
NOT_ISOLATED
```

T1 and T2 had strongly different trajectory content but identical trigger/timing. T3 differed in both content and geometric trigger. Do not interpret 101 versus 105 as a meaningful content-style effect.

## DeepMemory Text Record

First naturally exported records:

```text
T1: source eid == deep eid == 5
T2: source eid == deep eid == 5
T3: source eid == deep eid == 6
```

All first records:

```text
type: identity_anchor
compression_score: 0.4859
summary_length: 200
embedding_ref: null
```

Fresh `DeepMemoryStore` re-read confirmed textual persistence. The 200-character summary comes from production compression candidate truncation.

Freeze:

```text
FIRST_DEEP_TEXT_RECORD_WITH_UNCHANGED_THRESHOLDS:
DEMONSTRATED

PROVIDER_FREE_DEEP_TEXT_RECORD_FORMATION:
DEMONSTRATED
```

Do not call this an operational/retrievable DeepMemory yet. Use `persistent DeepMemory textual record` when precision matters.

## Milestone Separation

Milestones:

```text
M1: min-step gate crossed
M2: first authentic compression effect
M3: first short_path
M4: first long_path
M5: first persistent DeepMemory TEXT record
M6: first vector-indexed / retrievable DeepMemory
```

Measured:

```text
T1:
  M1: 100
  M2: 105
  M3: 105
  M4: 105
  M5: 105
  M6: NEVER REACHED

T2:
  M1: 100
  M2: 105
  M3: 105
  M4: 105
  M5: 105
  M6: NEVER REACHED

T3:
  M1: 100
  M2: 101
  M3: 101
  M4: 101
  M5: 101
  M6: NEVER REACHED

Condition A:
  M1: 100
  M2-M6: NEVER REACHED
```

The original harness did not define M6. This preservation note does.

## Vector Persistence Failure

Freeze:

```text
DEEPMEMORY_VECTOR_PERSISTENCE:
FAILED

DEEPMEMORY_TEXT_RECORD_FORMED_BUT_VECTOR_INDEX_FAILED:
DEMONSTRATED
```

Every first-deep record in T1/T2/T3 and the independent replication has:

```text
embedding_ref = null
```

Deep textual record persistence succeeded. Deep embedding/vector persistence failed.

## Windows MAX_PATH Cause

Freeze:

```text
DEEPMEMORY_EMBEDDING_PERSISTENCE_FAILURE_CAUSE:
WINDOWS_PATH_LIMITATION
```

Do not call this a production-path logic defect.

Measured path bracket:

```text
Windows usable traditional MAX_PATH length: 259 characters

T1/T2 embeddings directory:
  244 chars

T1/T2 manifest.json.tmp:
  262 chars
  FAILED

T3 embeddings directory:
  239 chars

T3 manifest.json.tmp:
  257 chars
  SUCCEEDED

T3 manifest.json:
  253 chars
  PRESENT

T3 shard_000000.npy:
  256 chars
  PRESENT, approximately 6 MB

T3 shard_000000.map.jsonl:
  262 chars
  FAILED

Largest observed successful path:
  257

Smallest observed failed path:
  262
```

Every observed file outcome agrees with that boundary. The five-character shorter T3 path explains why it progressed farther before failing. The `.tmp` suffix on atomic manifest writing explains why T1/T2 fail before `manifest.json` can be committed.

Production deployment paths are approximately 130 characters shorter. Therefore this is an experiment/harness filesystem-path limitation on Windows, not evidence that ordinary production data roots would fail.

## Export Failure Handling

Freeze:

```text
DEEPMEMORY_EXPORT_SILENTLY_TOLERATES_VECTOR_PERSISTENCE_FAILURE:
CODE_TRACED
```

`DeepMemoryStore.export` treats vector persistence as best-effort. When embedding writing fails:

```text
warning logged
embedding_ref remains null
text record still persists
export returns normally
compression log reports exported_deep = 1
source row is marked exported_deep = true
source strength becomes 0.1
```

This robustness/failure-handling behavior is a production observation. It is not the cause of the Windows path failure. Do not fix it here.

## Retrievability

Freeze:

```text
FIRST_RETRIEVABLE_DEEP_MEMORY_WITH_UNCHANGED_THRESHOLDS:
CONTRADICTED

PROVIDER_FREE_RETRIEVABLE_DEEP_MEMORY_FORMATION:
CONTRADICTED
```

Reason: `DeepMemoryStore._build_emb_matrix` skips records whose `embedding_ref is None`. With no vectors, `_emb_mat` has shape `(0, 384)`, and `DeepMemoryStore.query` returns `[]` unconditionally.

Therefore these textual records cannot enter normal deep vector retrieval, cannot reach source/beta filtering, cannot warm, cannot Spirit Return, cannot rank, and cannot render. Do not call these records operational DeepMemory.

## Source Embedding Export Path

Freeze:

```text
SOURCE_EMBEDDING_LOAD_FOR_EXPORT:
SUCCEEDED
```

The source embedding was loaded and supplied to `DeepMemoryStore.export`. T1/T2 then lacked a usable shard writer due to the earlier `manifest.json.tmp` path failure. T3 reached embedding append and failed on `shard_000000.map.jsonl`.

Thus:

```text
source vector availability: succeeded
DeepMemory textual record: succeeded
DeepMemory vector persistence: failed
```

## Provider-Free And Strict Embedding Claims

Freeze:

```text
PROVIDER_FREE_COMPRESSION_REACHABILITY:
DEMONSTRATED

PROVIDER_FREE_DEEP_TEXT_RECORD_FORMATION:
DEMONSTRATED

PROVIDER_FREE_RETRIEVABLE_DEEP_MEMORY_FORMATION:
CONTRADICTED

EMBEDDER:
ST_BGE_LIVED_USE_SEMANTIC

EMBEDDER_STRICT_MODE_ENFORCED:
DEMONSTRATED
```

Configuration:

```text
TORMENT_EMBED_PROVIDER=st
TORMENT_EMBED_MODEL=BAAI/bge-small-en-v1.5
TORMENT_EMBED_STRICT=1
```

HashEmbedding was not used in the completed runs. Provider text generation was not invoked. Fixed scripted assistant text stood in for provider-generated text, so do not generalize to provider behavior or natural human conversation.

## Hard Cap And Count Pressure

Freeze:

```text
HARD_CAP_ROUTE:
NOT_REACHED
```

Maximum graph size: 27

Count-overflow fallback threshold: 400

Private-memory hard cap: 10000

Neither was remotely approached. Do not attribute first compression to memory-count pressure.

## Multi-Session And Historical Boundaries

Freeze:

```text
MULTI_SESSION_REACHABILITY:
NOT_CHARACTERIZED_BY_V1

HISTORICAL_28_STEP_COMPARISON:
NOT_DIRECTLY_COMPARABLE
```

Each authoritative condition was one continuous worker process. No new evidence binds the earlier basin metric to this experiment's current step metric.

## Corrected Taxonomy

```text
NATURAL_LONG_MEMORY_REACHABILITY_V1

RESULT_SCOPE:
SCRIPTED_PROVIDER_FREE_COMPRESSION_AND_DEEP_TEXT_RECORD_REACHABILITY

DEFAULT_NEW_DEEP_FORMATION:
DISABLED_BY_DESIGN

DEFAULT_OFF_RUNTIME_CHECK_THROUGH_FIRST_FALLBACK_REGION:
DEMONSTRATED

COMPRESSION_MIN_STEP_GATE:
100_CODE_TRACED_AND_OBSERVED

ENABLED_FIRST_COMPRESSION_EFFECT:
DEMONSTRATED

FIRST_COMPRESSION_TRIGGER_T1:
corridor_exit @ 105

FIRST_COMPRESSION_TRIGGER_T2:
corridor_exit @ 105

FIRST_COMPRESSION_TRIGGER_T3:
cycle_stage_change @ 101

FIRST_COMPRESSION_TRIGGER_CLASS:
GEOMETRIC_NOT_FALLBACK

ENABLED_FIRST_SHORT_PATH:
DEMONSTRATED

ENABLED_FIRST_LONG_PATH:
DEMONSTRATED

FIRST_LONG_PATH_SOURCE_CLASS:
AUTOMATIC_IDENTITY_ANCHOR

FIRST_LONG_PATH_CAUSE:
IDENTITY_TIER_OVERRIDE

IDENTITY_ANCHOR_IS_AUTOMATIC_PRODUCTION_MEMORY:
YES

HARNESS_CREATED_OR_FORCED_IDENTITY_ANCHOR:
NO

ORDINARY_RELATIONAL_LONG_PATH_REACHABILITY:
NOT_DEMONSTRATED

ORDINARY_RELATIONAL_LONG_PATH_STRUCTURALLY_UNREACHABLE_BELOW_STEP_500:
CODE_TRACED_AND_CONSISTENT_WITH_OBSERVATION

FIRST_DEEP_TEXT_RECORD_WITH_UNCHANGED_THRESHOLDS:
DEMONSTRATED

FIRST_RETRIEVABLE_DEEP_MEMORY_WITH_UNCHANGED_THRESHOLDS:
CONTRADICTED

DEEPMEMORY_VECTOR_PERSISTENCE:
FAILED

DEEPMEMORY_TEXT_RECORD_FORMED_BUT_VECTOR_INDEX_FAILED:
DEMONSTRATED

DEEPMEMORY_EMBEDDING_PERSISTENCE_FAILURE_CAUSE:
WINDOWS_PATH_LIMITATION

DEEPMEMORY_EXPORT_SILENTLY_TOLERATES_VECTOR_PERSISTENCE_FAILURE:
CODE_TRACED

SOURCE_EMBEDDING_LOAD_FOR_EXPORT:
SUCCEEDED

PROVIDER_FREE_COMPRESSION_REACHABILITY:
DEMONSTRATED

PROVIDER_FREE_DEEP_TEXT_RECORD_FORMATION:
DEMONSTRATED

PROVIDER_FREE_RETRIEVABLE_DEEP_MEMORY_FORMATION:
CONTRADICTED

REINFORCEMENT_MATERIAL_TO_GRAPH_GROWTH:
DEMONSTRATED

REINFORCEMENT_MATERIAL_TO_FIRST_DEEP_REACHABILITY:
NOT_ISOLATED

TRAJECTORY_DEPENDENCE_OF_FIRST_DEEP_REACHABILITY:
NOT_ISOLATED

T1_REACHED_DEEP_TEXT_RECORD_VIA_IDENTITY_ANCHOR:
DEMONSTRATED

T2_REACHED_DEEP_TEXT_RECORD_VIA_IDENTITY_ANCHOR:
DEMONSTRATED

T3_REACHED_DEEP_TEXT_RECORD_VIA_IDENTITY_ANCHOR:
DEMONSTRATED

STYLE_INDEPENDENT_REACHABILITY:
NOT_ISOLATED

AUTOMATIC_ROW_CLASSES_OBSERVED:
seed_canon, identity_anchor, drift_correction

EXCHANGE_EQUALS_STEP:
DEMONSTRATED

FALLBACK_PERIODIC_STEP_201_REQUIRED:
CONTRADICTED

STEP_201_CODE_TRACE_STATUS:
CORRECT_AS_A_NO_EARLIER_EVENT_FALLBACK_EXPECTATION

HARD_CAP_ROUTE:
NOT_REACHED

MULTI_SESSION_REACHABILITY:
NOT_CHARACTERIZED_BY_V1

HISTORICAL_28_STEP_COMPARISON:
NOT_DIRECTLY_COMPARABLE

THRESHOLD_LOWERING:
NOT_USED

MANUAL_STEP_ADVANCEMENT:
NOT_USED

DIRECT_COMPRESSION_CALL_AS_AUTHORITY:
NOT_USED

PROVIDER:
NOT_INVOKED

EMBEDDER:
ST_BGE_LIVED_USE_SEMANTIC

EMBEDDER_STRICT_MODE_ENFORCED:
DEMONSTRATED

TRANSPORT_BOUNDARY:
IN_PROCESS_ENDPOINT_EQUIVALENT_LIVED_USE_PATH

INDEPENDENT_REPLICATION:
20260811T122627Z_IDENTICAL_TAXONOMY_AND_SUMMARIES

CONFIGURATION_BOUNDARY:
NON_DEFAULT_COMPRESSION_ENABLED

NATURAL_PREVALENCE:
NOT_MEASURED

DEEP_MEMORY_USEFULNESS:
NOT_TESTED

DEEP_MEMORY_HARMFULNESS:
NOT_TESTED
```

## Prohibited Interpretations

Do not claim:

```text
ordinary memories naturally enter Deep Memory around turn 100
Deep Memory becomes operational around turn 100
all three conversation styles reach operational Deep Memory equally
step-201 trace was wrong
compression is naturally reachable under default compression-off configuration
population prevalence
typical human exchange count
provider usefulness
Deep Memory usefulness
Deep Memory harmfulness
```

## Strongest Allowed Claim

Scripted provider-free, in-process-endpoint-equivalent lived use reached authentic production compression with unchanged compression thresholds after the min-step gate opened at 100. Production geometric EventDetector triggers fired at steps 101-105. Ordinary relational memories short-pathed, while one automatically generated identity anchor per trajectory entered long_path through the unconditional identity-tier route and produced a persistent 200-character DeepMemory textual record. Vector persistence then failed because the experiment's deeply nested Windows data paths exceeded traditional MAX_PATH, leaving `embedding_ref = null` and the records mechanically unretrievable. Thus V1 demonstrates compression, short-path processing, identity-tier long-path export, and persistent deep textual record formation, but not ordinary relational long-path maturity or operational vector-retrievable DeepMemory.

## Raw Artifact Immutability

Do not alter:

```text
20260811T123033Z authoritative result
20260811T122627Z complete replication
20260811T122505Z failure provenance
20260811T122548Z failure provenance
```

The SHA-256 identities for the harness, authoritative result, replication result, and this preservation note are computed by the preservation operation and returned separately. This note intentionally does not embed its own final SHA-256.
