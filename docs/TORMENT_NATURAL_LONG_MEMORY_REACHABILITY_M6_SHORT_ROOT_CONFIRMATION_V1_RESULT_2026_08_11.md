# TORMENT Natural Long Memory Reachability M6 Short-Root Confirmation V1 Result

Preservation date: 2026-08-11

Experiment: `NATURAL_LONG_MEMORY_REACHABILITY_M6_SHORT_ROOT_CONFIRMATION_V1`

Alias in sequence: Experiment #4A

Purpose: remove the Experiment #4 Windows path-depth confound and test M6 only.

## Baseline And Scope

Baseline:

```text
HEAD == origin/main == 26be69c896560b85b6af870652bad96ff455c336
Subject: test(lived-use): preserve natural long-memory reachability
```

Harness:

```text
scripts/natural_long_memory_reachability_m6_short_root_confirmation_v1.py
```

Authoritative artifact:

```text
outputs/experiments/natural_long_memory_reachability_m6_short_root_confirmation_v1/20260811T134119Z/natural_long_memory_reachability_m6_short_root_confirmation_v1_result.json
```

Complete replication artifact:

```text
outputs/experiments/natural_long_memory_reachability_m6_short_root_confirmation_v1/20260811T133933Z/
```

Configuration: `NON_DEFAULT_COMPRESSION_ENABLED`

Provider: `NOT_INVOKED`

Embedder: `ST / BAAI/bge-small-en-v1.5`

Transport boundary: `IN_PROCESS_ENDPOINT_EQUIVALENT_LIVED_USE_PATH`

No compression, routing, embedding, reinforcement, EventDetector, identity-anchor, or DeepMemory thresholds were changed. No threshold environment variables were set.

Freeze:

```text
SINGLE_VARIABLE_MANIPULATION:
DEMONSTRATED
```

Only `TORMENT_DATA_DIR` differed from Experiment #4 T3 among the effective environment variables compared for this sequel.

## Causal Comparison

Experiment #4 T3 and #4A used byte-identical first 101 exchanges:

```text
trajectory SHA:
18c5b108dece5fc61a5d9a222d5b0863f77d1ee8dc55967b3043cdac0c37f1ce
```

Both observed:

```text
trigger: cycle_stage_change @ step 101
candidates evaluated: 14
short/compressed: 13
exported deep: 1
graph accounting: 13 NEW_SOURCE_ROW, 88 REINFORCEMENT, 101 exchanges, 15 graph rows
first long-path source: eid 6, automatic identity_anchor
born_step: 4
age: 97
strength: 0.79 -> 0.1
compression_score: 0.4859
route cause: identity-tier override
source vector SHA-256:
a65f4c74ac6c7f103c657eebdcb1e794f469b640a8f57d352de8f402757f84da
```

The material destination path changed:

```text
Experiment #4 failing deep map path: 262 chars
Experiment #4A deep map path: 108 chars
```

Freeze:

```text
EXPERIMENT_4_M6_FAILURE_CAUSED_BY_WINDOWS_PATH_DEPTH:
DEMONSTRATED
```

## Milestones

```text
M1: step 100
M2: step 101
M3: step 101
M4: step 101, eid 6
M5: step 101, eid 6
M6: step 101, eid 6
```

M6 requires persistent vector-indexed retrievability and was demonstrated.

## DeepMemory Persistence

Freeze:

```text
M5_DEEP_TEXT_RECORD:
DEMONSTRATED

DEEPMEMORY_VECTOR_PERSISTENCE:
DEMONSTRATED

EMBEDDING_REF_NON_NULL:
DEMONSTRATED

M6_VECTOR_INDEXED_RETRIEVABLE_DEEPMEMORY:
DEMONSTRATED
```

First DeepMemory:

```text
eid: 6
source eid: 6
source type: identity_anchor
compression_score: 0.4859
summary length: 200
embedding_ref: shard 0, row 0, dim 384
manifest: total_rows 1, next_row 1, dim 384
map: row 0, eid 6, kind deep_compressed
```

## Vector Identity

Freeze:

```text
DEEP_VECTOR_MATCHES_SOURCE_VECTOR:
DEMONSTRATED

SOURCE_AND_DEEP_VECTOR_BIT_IDENTICAL_ACROSS_EXPERIMENT_4_AND_4A:
DEMONSTRATED

DEEP_VECTOR_IS_COPIED_FULL_SOURCE_VECTOR:
DEMONSTRATED_UNDER_LIVED_USE_ST_BGE

REFERENCED_SHARD_ROW_IS_DENSE_NOT_PREALLOCATED:
DEMONSTRATED
```

Observed vector identity:

```text
source private row SHA-256:
a65f4c74ac6c7f103c657eebdcb1e794f469b640a8f57d352de8f402757f84da

DeepMemory row SHA-256:
a65f4c74ac6c7f103c657eebdcb1e794f469b640a8f57d352de8f402757f84da

exact element equality: true
max_abs_diff: 0.0
deep row: 384 / 384 non-zero, norm 1.0
control/preallocated row 1: 0 / 384 non-zero, norm 0.0
```

This demonstrates a genuine persisted vector, not merely a preallocated shard.

## Fresh Store

Freeze:

```text
FRESH_STORE_DEEP_QUERY_RETURNS_NEW_EID:
DEMONSTRATED
```

Fresh `DeepMemoryStore`:

```text
matrix shape: [1, 384]
eid list: [6]
query using source vector: returns eid 6
similarity: 1.0
production threshold: 0.4
```

No semantic relevance claim is authorized from this self-similarity measurement.

## Fabric Query Boundary

Freeze:

```text
DEEP_STORE_VECTOR_RETRIEVABILITY:
DEMONSTRATED

FABRIC_DEEP_LANE_RETURNS_NEW_EID:
DEMONSTRATED_UNDER_FORCED_DEEP_HEADROOM

LIVED_USE_DEFAULT_MEMORYPLAN_DEEP_RETRIEVAL:
NOT_TESTED

FINAL_RENDERED_SURFACE:
NOT_TESTED
```

The optional Fabric query used `top_k=80` and a crafted MemoryPlan approximating:

```text
core: 1
relational: 1
deep: 80
```

This is not evidence for ordinary lived-use or default MemoryPlan retrieval. `assemble_context` was not called.

The optional Fabric probe also created post-M6 warmth state:

```text
POST_M6_WARMTH_CREATED_BY_OPTIONAL_PROBE:
DEMONSTRATED

warmth: 0.2
appearance_count: 1
```

This post-M6 state must not be used as M6 evidence.

## Windows Failure

Freeze:

```text
SHORT_ROOT_PATH_CONFUND_REMOVED:
DEMONSTRATED

WINDOWS_MAX_PATH_FAILURE_RECURS:
NO
```

Maximum relevant path in the authoritative #4A run:

```text
108
```

No captured warnings:

```text
deep memory shard init failed
deep memory embedding write failed
```

`manifest.json.tmp` being absent after success is normal atomic-write cleanup.

## Provider-Free Claim

Freeze:

```text
PROVIDER_FREE_RETRIEVABLE_DEEP_MEMORY_FORMATION:
DEMONSTRATED
```

Scope:

```text
scripted provider-free
in-process-endpoint-equivalent lived use
compression non-default enabled
```

Do not generalize this to natural-user prevalence.

## Ordinary Relational Boundary

Freeze:

```text
ORDINARY_RELATIONAL_LONG_PATH_REACHABILITY:
NOT_TESTED_IN_THIS_SEQUEL
```

#4A does not extend Experiment #4's relational-memory result.

## Replication

Reclassification:

```text
INDEPENDENT_REPLICATION:
20260811T133933Z_SAME_VECTOR_SAME_MILESTONES
```

`20260811T133933Z` is a complete successful short-root run. Its raw JSON contains the older classifier underclaim:

```text
SHORT_ROOT_PATH_CONFUND_REMOVED:
NOT_DEMONSTRATED
```

The raw historical JSON was not rewritten. The preservation interpretation corrects the classifier provenance: the underlying run has all M6 criteria true, the same trigger, the same eid, the same vector digest, and the same short-root success.

## Evidence Preservation

The external short roots contain shard bytes not contained in the result JSON. The original external roots remain authoritative originals and were not deleted or modified:

```text
C:\t\n4m6\20260811T134119Z
C:\t\n4m6\20260811T133933Z
```

Byte-preserving copies were created under the repo's gitignored experiment output area. The shorter evidence path avoids recreating the Windows path-depth confound during preservation.

Authoritative short-root evidence:

```text
outputs/experiments/n4m6_m6_short_root_evidence/20260811T134119Z/
copy root: outputs/experiments/n4m6_m6_short_root_evidence/20260811T134119Z/r/
manifest: outputs/experiments/n4m6_m6_short_root_evidence/20260811T134119Z/short_root_evidence_manifest.json
manifest SHA-256: 2d5587a735263dcdd2b2175378a553bfcdcc86bfaf16772bd81c1598bf7973f3
verification: outputs/experiments/n4m6_m6_short_root_evidence/20260811T134119Z/short_root_evidence_verification.json
verification SHA-256: 6bd08466cf26684c6cef4a6b21ec2e860400c5f1eb26e3cc3197a8cef8ec0fd4
file count: 26
all original-vs-copy SHA-256 checks: true
```

Replication short-root evidence:

```text
outputs/experiments/n4m6_m6_short_root_evidence/20260811T133933Z/
copy root: outputs/experiments/n4m6_m6_short_root_evidence/20260811T133933Z/r/
manifest: outputs/experiments/n4m6_m6_short_root_evidence/20260811T133933Z/short_root_evidence_manifest.json
manifest SHA-256: d1a8d7846a3e445a998530a0ef3a3f236b76f0a9a09bfe9e0a311f11c9f40ac6
verification: outputs/experiments/n4m6_m6_short_root_evidence/20260811T133933Z/short_root_evidence_verification.json
verification SHA-256: e4821a630da2a7a28d45e321547d336552e423576838e9516ff6bf958042f0c0
file count: 26
all original-vs-copy SHA-256 checks: true
```

Selected authoritative copied evidence hashes:

```text
deep_memory/memories.jsonl:
a84b73ca69e3cce4c325410011daa4268671c61d7757d6548d5974feb91d6783

deep_memory/embeddings/manifest.json:
10389cc7f783d30ead6c1d1d514074a7a69c1c6a1697b850a7674d6055750665

deep_memory/embeddings/shard_000000.npy:
6eae476c93a6677770a13645c37186e4b7070392708c644333177851c684178f

deep_memory/embeddings/shard_000000.map.jsonl:
2d18f50c9798ec7418d6cd8f84136fcd340ee396a9d71be1c2dcfc7d89702dea

private/embeddings/shard_000000.npy:
115a0f1568288ca460a55dec24db763277e6351a72138d038726ff623c6eba24

private/embeddings/shard_000000.map.jsonl:
a33bb0f4f65eeee069bb9a06327231e277341b07326c08c31cfa6ff8338e1d4a
```

Selected replication copied evidence hashes:

```text
deep_memory/memories.jsonl:
a9ffdd43ee08818d366c0bc70c1c93f93ee372a96a682e2aeac54b55b4748d71

deep_memory/embeddings/manifest.json:
10389cc7f783d30ead6c1d1d514074a7a69c1c6a1697b850a7674d6055750665

deep_memory/embeddings/shard_000000.npy:
6eae476c93a6677770a13645c37186e4b7070392708c644333177851c684178f

deep_memory/embeddings/shard_000000.map.jsonl:
013d48301e3465efd69226d89c34e9b4611023030023d3b293b2416e4d3f3abc

private/embeddings/shard_000000.npy:
115a0f1568288ca460a55dec24db763277e6351a72138d038726ff623c6eba24

private/embeddings/shard_000000.map.jsonl:
27d559e85c7ba39f8f9fda272c7ec4e7f5e86a720f0f345b146ce3d4e16e3de6
```

## SHA-256 Identities

```text
harness:
10401204ee66c3920f95cf767b17669e36e52b02214b61d382d548d9fa987497

authoritative result JSON:
e777346a5503f1a9e99bad48e5ce795f2f563f5f1c05d33112e9a74c49c087b1

replication result JSON:
eafbf5585c6d3b22441d8af673285821109dc2990ab92e8d54fabfa6c47b63d1
```

The preservation note's own SHA-256 is intentionally not embedded in this file.

## Prohibited Overclaims

Do not claim:

```text
ordinary relational DeepMemory reachability demonstrated
Deep Memory generally wakes at turn 101
real users naturally reach Deep Memory at turn 101
ordinary companion/default MemoryPlan retrieval demonstrated
final rendered deep context demonstrated
identity-first behavior is optimal
Deep Memory improves character behavior
provider usefulness
natural prevalence
```
