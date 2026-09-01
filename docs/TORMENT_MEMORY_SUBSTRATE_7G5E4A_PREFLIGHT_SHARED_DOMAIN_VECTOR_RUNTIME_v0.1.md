# TORMENT Memory Substrate 7G5E4A — Shared-Domain and Vector Runtime Preflight

## Status and boundary

Starting revision: `902133fb01a59d91e3cc0b65b88547d2e49f3835`.

This is an archaeology and characterization freeze. It neither selects native
storage, enables native reads or writes, admits shared workspaces, changes the
kernel, nor moves bridges into SQLite.

`KERNEL_MATHEMATICS_CHANGED = NO`
`KERNEL_VECTORISATION_REPLACED = NO`
`KERNEL_DYNAMIC_BEHAVIOR_CHANGED = NO`
`NATIVE_ACTIVE = NO`
`DUAL_WRITE = NO`
`DUAL_READ = NO`
`CUTOVER_OPENED = NO`

The frozen sources are `torment_service/memory_kernel.py`,
`torment_service/kernel/**`, `torment_service/memory_graph.py`, and the
current Fabric orchestration. An ANN, HNSW index, or external vector database
is not a compatible replacement proposal.

## Current query pipeline

`TormentFabric.query()` currently follows this order:

1. Fabric asks the kernel-owned embedder for `qemb`, verifies the workspace
   dimension, then passes it to `DomainRouter.rank_domains()`.
2. `DomainRouter` asks each domain's `MotifRegistry` for its domain centroid,
   applies the existing cosine law, descending score sort, and selects two
   domains. An explicit requested domain is moved to the front and the list is
   again capped at two.
3. Fabric calculates the core, relational, and deep lane budgets from the
   optional MemoryPlan.
4. The private lane calls that agent's `MemoryGraph.search(query_text, ...)`.
5. Each selected primary shared domain calls that domain's
   `MemoryGraph.search(query_text, ...)`.
6. If bridge peeking is requested, `BridgeRegistry.relevant_to_domains()` is
   filtered by rejected/approved/confidence policy and at most two external
   domains are searched through their shared `MemoryGraph` lanes.
7. The deep lane receives the already-computed `qemb` and fills remaining
   headroom only.
8. The lanes are merged; default-memory-class filtering, motif alignment,
   conflict treatment, continuity, Character, SRG, provenance, reinforcement,
   and MemoryPlan lane weighting contribute to the final score. Governance
   filtering occurs before LLM-facing results are returned.

There is one important implementation fact to preserve or deliberately
reconcile in a later bounded change: private and shared `MemoryGraph.search`
currently call their own configured embedder with `query_text` again. The
initial `qemb` is used for domain routing and deep retrieval. A future vector
runtime must not silently replace these calls with the earlier `qemb` without
first freezing the call-count and dynamic-embedder behavior.

## Fast-recall compatibility law

For `TORMENT_GRAPH_EMB_CACHE` enabled, `MemoryGraph` owns these process-local
fields:

- `_emb_by_eid`: graph-local EID to normalized vector;
- `_eid_list`: ascending numeric EID order;
- `_emb_mat`: an `N x D` row-normalized `float32` matrix; and
- `_index_dirty`: causes a reload/rebuild before the next cached query.

`_normalize()` converts input to flat `float32`, pads or truncates to the
configured dimension, computes `float(np.linalg.norm(v) + 1e-12)`, and returns
`(v / norm).astype(np.float32)`. `_load_embeddings_into_ram()` loads every
available graph embedding, skips unavailable or invalid vectors, then calls
`_rebuild_matrix()`. The rebuild sorts graph-local EIDs and stacks rows as
`float32`. `_ensure_index()` performs that load/rebuild if dirty or absent.

Both cached `search()` and `search_by_embedding()` normalize the query with
this exact helper, calculate:

```text
scores = (row_normalized_float32_matrix @ normalized_float32_query).astype(float32)
```

They use `np.argsort(-scores)` when `N <= k`; otherwise they use:

```text
candidate = np.argpartition(-scores, k - 1)[:k]
order = candidate[np.argsort(-scores[candidate])]
```

Only those raw-score candidates are then loaded and filtered. `min_score`,
type, user, and (for `search_by_embedding`) canon filtering can therefore
return fewer than `k` rows. Half-life decay is applied after candidate
selection, and returned rows are re-sorted only by decayed score. The cache's
tie behavior is the current NumPy `argpartition`/`argsort` behavior over the
ascending-EID matrix; it must not be replaced with a UUID, rowid, or invented
tie breaker.

The cache-disabled fallback is not the fast-recall contract: it walks entity
insertion order, normalizes one vector at a time, then sorts Python tuples by
score.

## Durable state versus live geometry

SQLite is the durable authority for current core-memory objects, revisions,
namespaced EID aliases, runtime-order evidence, qualified representations,
and relationships. A live vector matrix is rebuildable process state only. It
is neither a memory owner nor an independent source of readiness.

The current `NativeMemoryCompatibilityFacade.search_by_embedding()` is a
correctness-oriented durable reader, not the live-cache replacement. It
normalizes candidate and query vectors as `float64` without MemoryGraph's
`+1e-12` float32 rule, sorts durable results with explicit EID and
representation-ID tie breakers, and has no RAM matrix. The 7G5E4A
characterization test proves that a small nonzero vector yields a materially
different score from the MemoryGraph law. It also proves that a matrix rebuilt
from the same qualified native raw bytes *does* match byte-for-byte when it
uses MemoryGraph normalization and matrix operations exactly.

## Frozen native vector-runtime design

The later implementation target is a read-only, process-local
`NativeMemoryVectorRuntime` with one cache per explicit lane key:

```text
(workspace_id, scope_kind, qualifier, legacy_source_namespace_id,
 representation class/generation/contract/encoding/dtype/dimension)
```

`qualifier` is `agent_id` for `PRIVATE_AGENT` and `domain_id` for
`SHARED_DOMAIN`. A bare EID is never a cache key.

Each cache row must retain, alongside its normalized `float32` matrix row:

```text
namespaced EID
native object ID
current object revision ID and ordinal
qualified representation ID
selected integrity-measurement witness
```

Rebuild steps are fixed:

1. validate the prepared STAGING binding and one explicit
   `NativeMemoryRuntimeScope`;
2. validate namespace EID aliases against
   `memory_runtime_enumeration_orders` (the existing native runtime-order
   carrier); fail closed on disagreement;
3. select only current `LEGACY_CORE_NODE` objects in that source namespace;
4. read only current `READY` + `USABLE` + integrity-`MATCH`
   `COMPAT_EMBEDDING/1/compat-embedding-v1/RAW_VECTOR/float32` rows;
5. retain the raw vector witnesses, sort cache rows by numeric EID, and apply
   MemoryGraph's exact normalization and matrix construction; and
6. atomically replace the in-process snapshot only after all row witnesses
   validate.

The memory-runtime enumeration carrier validates completeness; it does not
override MemoryGraph's ascending-EID matrix order. Missing, failed,
withheld, withdrawn, or reconciliation-required representations are omitted
from vector geometry exactly as missing legacy graph embeddings are omitted.

Before a cached query, the runtime must validate its durable snapshot witness.
If an object revision, representation readiness/disposition, measurement, EID
alias, or enumeration row no longer matches, it must discard the snapshot and
rebuild from SQLite. If rebuild cannot establish a complete, self-consistent
snapshot, that lane returns no cached result rather than serving stale vectors.

## Cache coherence events

The later storage owner must invalidate or replace only the affected lane
after these durable facts publish:

| Durable event | Required cache action |
| --- | --- |
| New memory source plus READY representation | rebuild/add its lane row |
| Reinforcement successor | remove/rebuild the old-revision row; include R2 only after its qualified representation is READY |
| New READY representation | rebuild/add the source's current row |
| Withdrawal, failed verification, or reconciliation disposition | remove/rebuild the source row |
| Completion of migration/admission | rebuild every admitted lane |
| Cold process recovery | rebuild on demand from SQLite only |
| Motif split | no memory-vector invalidation by itself |

Motif geometry and membership retirement remain separate from memory-vector
geometry. A motif-only split must not rebuild every memory vector.

## Multi-lane and shared-domain topology

One native core can structurally hold simultaneous private-agent and
shared-domain lanes: the existing runtime-binding tests already validate
multiple `NativeMemoryRuntimeScope` values and source-namespace uniqueness.
This is not permission to activate or admit them yet.

Every admitted lane requires distinct, explicit values for:

| Scope | Identity facts |
| --- | --- |
| Private agent | workspace ID, `PRIVATE_AGENT`, agent ID, source namespace, memory identity namespace, semantic scope, motif alias namespace, motif identity namespace, membership identity namespace, idempotency namespace, runtime-order carrier |
| Shared domain | workspace ID, `SHARED_DOMAIN`, domain ID, source namespace, memory identity namespace, semantic scope, motif alias namespace, motif identity namespace, membership identity namespace, idempotency namespace, runtime-order carrier |

The source namespace and runtime-order carrier make overlapping numeric EIDs
safe. A shared domain and a private agent may both have EID `0`; they are never
the same cache row or lookup key.

7G5E1's descriptor and execution loops are deliberately single private-agent
profile machinery, and explicitly reject shared-domain admission. Extending
it is not a flag change: a later admission slice needs a multi-scope descriptor
containing ordered lane plans, snapshot roots for each
`workspaces/<workspace>/domains/<domain>/shared` MemoryGraph, and per-lane
namespace/alias/order witnesses. It must project observed shared motifs without
forcing a split and then prove cold recovery across more than one source
namespace before it can be enabled.

## Shared write and domain-geometry seams

Current direct `ingest(scope="shared")` leaves kernel processing, provenance,
affect/SRG preparation, embedder selection, and domain ranking unchanged. It
chooses `ws.shared_graphs[chosen_domain]`, writes the graph memory, attaches
the domain `MotifRegistry`, computes symbol/resonance data, and flushes the
graph record. Private reinforcement is intentionally not applied to shared
writes.

The proposal paths (`process_proposals` and `decide_proposal`) independently
write the selected domain's shared graph, attach its motif registry, then
refresh bridge suggestions. A future native shared storage adapter must
replace only these graph/motif storage-owner calls after all existing
pre-storage facts are prepared. Kernel, DomainRouter, proposal governance,
post-write consumers, Character, SRG, and bridge policy remain external.

DomainRouter itself remains in process. The future backend-neutral port is a
read-only domain-geometry provider:

```text
domain_centroid(domain_id, expected_dimension) -> float32 vector
```

The legacy adapter delegates to `MotifRegistry.domain_centroid`; the native
adapter delegates to `NativeMotifRuntimeReader.domain_centroid` with that
domain's explicit motif-alias namespace and semantic scope. DomainRouter keeps
its current zero-vector check, cosine calculation, descending sort, and
top-k behavior.

## Bridges remain external

`BridgeRegistry` remains the owner of external bridge records and current
rejected/approved/confidence behavior. A future alias-safe bridge resolver
must resolve a bridge endpoint from this full key:

```text
(workspace_id, domain_id, external runtime motif ID, domain motif-alias namespace)
```

It may verify that the resolved native motif belongs to the matching domain
scope, but it must not create a SQLite memory relationship or collapse a
cross-domain bridge into a bare motif ID. Bridge peeking remains a policy that
selects extra shared lanes; it is not a memory relationship.

## 7G5E4A exclusions and next prerequisites

Not implemented here: native vector-runtime production wiring, shared-domain
admission, shared write routing, a production selector, native activation,
dual reads/writes, bridge migration, ANN semantics, or any kernel change.

Before a later implementation slice may wire a native vector runtime, it must
provide an explicit query-vector invocation contract, a runtime snapshot
witness/invalidation mechanism, multi-scope admission topology, and full
private/shared/bridge query parity evidence.
