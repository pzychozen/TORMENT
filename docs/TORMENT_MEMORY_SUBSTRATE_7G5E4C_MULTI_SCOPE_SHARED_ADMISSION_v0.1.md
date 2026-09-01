# TORMENT Memory Substrate 7G5E4C

## Multi-scope existing-workspace admission

7G5E4C adds the qualification-only `EXISTING_WORKSPACE_MULTI_SCOPE_CORE`
profile. It admits one pre-existing workspace into one STAGING SQLite core
with exactly one private-agent lane and one or more shared-domain lanes.
It does not alter the qualified 7G5E1 single-private request or service.

The public boundary is `ExistingWorkspaceNativeMultiScopeAdmissionService`.
Its request contains an ordered tuple of immutable
`ExistingWorkspaceNativeLanePlan` values. Every plan carries the actual graph
path, source namespace ID and key, memory namespace, semantic scope, all motif
namespaces, idempotency namespace, representation lane binding, and motif
domain. It never infers a namespace from a path or a numeric EID.

The descriptor order is administrative only: private agent ID first, then
shared-domain IDs in lexical order. It is not a memory ranking, motif-process,
or vector-row order.

## Frozen source and B-series coordination

For every lane the coordinator freezes an independent current-nodes snapshot,
embedding evidence, workspace lock, and the precise domain `motifs.json` that
owns that lane's motif registry. Each manifest has its own source namespace,
snapshot identity, digest, and lane-local source fingerprint. A workspace-wide
tree fingerprint is also pinned. Any byte change in the workspace before a
resume is refused; source files, embeddings, motifs, BridgeRegistry,
CharacterStore, checkpoints, and trajectories are never written by admission.

Each lane then uses the established B1, B2, B3A, and B4A writers with its own
snapshot and idempotency namespace. Captured bytes are reused; no re-embedding
is performed to reconcile a lane disagreement. The common workspace lock is
validated once, while every lane is independently bound to that same qualified
`COMPAT_EMBEDDING/1` raw-float32 identity.

B5 is a workspace closure, not a readiness claim for the first successful
lane. The private lane invokes the existing full B5 service. Shared lanes use
the same B1 and B5 memory/motif reader postconditions plus the whole-core
invariant in a read-only shared-lane closure. All scopes are then constructed
together in one STAGING memory binding and one routing capability. The existing
post-write adapter remains private-only, so no shared write route is created
merely to make a B5 check pass. A descriptor changes to `ADMISSION_COMPLETE`
only after every lane and this joint binding close.

Every lane serializes the same qualified representation-lane identity that is
pinned at the workspace level; a request or recovered descriptor with a
different lane is refused. Cold recovery also revalidates the complete,
canonical lane set, its namespace uniqueness, representation bindings, and
lane-plan digest before opening readers.

An interrupted workspace may therefore contain useful staging evidence from
earlier lanes, but it is not recoverable as ready. B2, B3A, B4A, B5, and
lost-response retries are idempotent under their explicitly namespaced keys.

## Recovery and retained owners

`recover_existing_workspace_native_multi_scope_runtime` accepts only a
complete descriptor, exact core, and exact representation lane. It reconstructs
read-only private/shared `NativeMemoryRuntimeScope` and
`NativeFabricRoutingScope` values, offering `lookup_private(agent_id)` and
`lookup_shared(domain_id)`. Each recovered lane can independently create a
`NativeMemoryVectorRuntime` using a caller-owned matching embedder; no legacy
graph, embedding shard, motif file, selector, or writer is retained.

Character seed continuity remains private-only and `CharacterStore` remains an
external owner. Shared lanes do not receive Character semantics. Checkpoints,
trajectory evidence, BridgeRegistry, and deep memory likewise remain external.

Bridge observation reads the external registry without moving it into SQLite.
Each endpoint is recorded as either an explicit namespace-qualified native
motif resolution or an `UNADMITTED_DOMAIN` observation. A bridge is never
created as a SQLite relationship.

## Qualification evidence

`tests/test_substrate_existing_workspace_multi_scope_admission.py` creates the
load-bearing workspace by launching normal `python -m torment_service` and
using regular HTTP workspace, agent, private-ingest, and shared-ingest routes.
It then uses the normal external BridgeRegistry owner to record a bridge. The
test freezes a legacy EID-zero characterization for private, research, and
engineering lanes after service creation, proving that numeric EID overlap is
isolated by source namespace rather than prohibited globally.

It verifies per-lane native memory/motif/vector parity, raw vector-matrix
bytes, legacy/native search candidates, raw scores, and top-k order,
domain-centroid parity, cross-domain motif-alias refusal, interruption,
source-change refusal, lost B5 response recovery, descriptor removal/insertion
tamper refusal, wrong-core and wrong-lane refusal, and fresh-interpreter cold
readers after legacy source removal. Each recovered private/shared runtime is
queried twice to prove its warm B1 matrix is reused rather than a whole-core
query cache being substituted.

## Boundary declaration

```text
KERNEL_FILES_CHANGED = 0
KERNEL_BEHAVIOR_CHANGED = NO
FABRIC_PRODUCTION_WIRING_CHANGED = NO
PRODUCTION_SELECTOR_ADDED = NO
NATIVE_ACTIVE = NO
DUAL_WRITE = NO
DUAL_READ = NO
CUTOVER_OPENED = NO

BRIDGES_REMAIN_EXTERNAL = YES
CHARACTERSTORE_REMAINS_EXTERNAL = YES
SHARED_WRITES_OPENED = NO
```
