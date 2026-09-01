# 7G5E4D-D6 shared compression / deep-memory boundary

## Scope and disposition

D6 starts at `9dc6ed7 Repair shared Character seed scope isolation`.  It
examines the final isolated optional post-write family, compression and deep
memory, without changing a compression equation, a kernel equation, the
public ingest backend, a selector, activation, dual read/write, or the deep
memory storage format.

The qualified result is deliberately narrow:

```text
DEFAULT_COMPRESSION_DISABLED_PROFILE = QUALIFIED
ENABLED_SHARED_COMPRESSION = BLOCKED
```

`NativePostWriteQualificationProfile.core_staging_with_shared_compression_disabled_noop()`
is an explicit shared-only D6 profile.  It may be prepared and run only when
the live Fabric owner has `owner._compress_enable is False` (the resolved
`TORMENT_COMPRESS_ENABLE=false` setting).  The run repeats that check, so a
deployment that becomes enabled after preparation refuses before effects; it
does not silently continue with a disabled native implementation.

For the qualified disabled path, the adapter returns before it opens the
native core database or binds a legacy post-write consumer.  It consequently
performs no source validation, candidate enumeration, motif/coherence read,
core successor, external deep-store access, external deep-store creation,
vector invalidation, or external compression log write.  This applies equally
to `CREATED_NEW`, reinforcement, and `NO_WRITE` contexts.

```text
SHARED_COMPRESSION_DISABLED_NOOP = PASS
ZERO_CANDIDATE_ENUMERATION = YES
ZERO_CORE_MUTATION = YES
ZERO_DEEP_STORE_MUTATION = YES
ZERO_VECTOR_INVALIDATION = YES
```

This is a semantic no-op rather than a refusal.  An enabled owner is refused
because D6 has not represented that feature safely.

## Frozen legacy topology

The legacy post-write adapter invokes `_run_compression(context)` after the
checkpoint phase when both `owner._compress_enable` and the minimum-step gate
are true.  It passes only `context.workspace_id`, `context.agent_id`, the
existing `tri_mod`, and `context.step` to `try_compress()` and
`check_hard_cap()`; it never passes `context.scope`, `context.eid`, the shared
domain, or the source record's motif IDs.

`try_compress()` and `check_hard_cap()` derive the composite private-agent key
`TormentFabric._agent_key(workspace_id, agent_id)`.  They read
`private_graphs[key]`, own `EventDetector`, executor history, and deep-store
cache state at that key, and use the private agent's `motifs.json` for the
coherence field.  A shared post-write trigger therefore wakes the specified
agent's private compression lane; it does not compress the just-written shared
memory.

| Required fact | Frozen legacy value for a shared trigger |
| --- | --- |
| `TRIGGER_SCOPE` | Shared source domain (`FabricPostWriteContext.scope = shared`). |
| `COMPRESSION_CANDIDATE_SCOPE` | Private agent graph keyed by `(workspace_id, agent_id)`. |
| `SHORT_PATH_TARGET_SCOPE` | The same private agent graph entity. |
| `LONG_PATH_SOURCE_SCOPE` | The same private agent graph entity. |
| `DEEP_STORE_OWNER` | External `workspaces/<workspace>/agents/<agent>/deep_memory`, cached by the same private-agent key. |
| `DEEP_RECORD_IDENTITY` | Bare private-graph `eid`, also used as the deep JSONL index and embedding-shard EID. |
| `CORE_SUCCESSOR_TARGET_SCOPE` | Existing private graph entity, mutated through `MemoryGraph.update_payload()`. |

There is no legacy operation that interprets a shared EID as a private EID:
the shared source EID is not supplied to compression at all.  Likewise, the
private coherence read is not made against the shared source lane.  The actual
boundary is instead an unrepresented cross-scope trigger: a shared source can
cause an unrelated private lane to perform candidate reads and mutable work.
No D6 mapping, implicit target selection, or shared-to-private EID projection
is invented to reproduce that behavior natively.

## Trigger, candidate, and hard-cap laws

The existing `EventDetector` remains wholly unchanged.  Its emergency tear,
corridor exit, cycle-stage change, count overflow, periodic trigger, cooldown,
and hard-cap handling still operate only within the private-agent compression
lane described above.  Kernel and `tri_mod` values remain observables only.

```text
COMPRESSION_TRIGGER_MATH_CHANGED = NO
COMPRESSION_MATHEMATICS_CHANGED = NO
```

If the feature were ever qualified for an enabled shared trigger, the native
read port can enumerate a *claimed namespace* in qualified runtime order.
That fact is insufficient for D6: the legacy candidate set is a separately
selected private graph, including its private motif/coherence file and
private-agent EventDetector state.  No enabled candidate-parity assertion is
made and no SQL cosine scan, new candidate scorer, or second hard-cap path is
added.

```text
SHARED_COMPRESSION_CANDIDATE_PARITY = BLOCKED
SHARED_HARD_CAP_COMPRESSION_PARITY = BLOCKED
```

## Short-path and long-path boundaries

The legacy short path mutates the existing private graph entity.  It applies
the existing tier multiplier and writes `strength`, `compressed`,
`compressed_step`, `compression_route = short_path`, `compression_score`, and
`compression_tier` with `MemoryGraph.update_payload()`.

The native typed-memory-successor service is intentionally closed to the
identity-anchor lifecycle patch.  It cannot encode the complete compression
patch.  A separate compatibility port has a generic flexible payload patch,
but it is explicitly generic and D6 is prohibited from treating it as a new
typed compression successor.  D6 therefore creates neither a generic payload
API nor a new object/revision path.

```text
SHARED_COMPRESSION_SHORT_PATH_PARITY = BLOCKED
CORE_SUCCESSOR_TARGET_SCOPE = UNREPRESENTED_FOR_ENABLED_SHARED_TRIGGER
```

For legacy long path, ordering is load-bearing and remains characterized:

```text
1. load the private graph entity's embedding when available
2. DeepMemoryStore.export(candidate, embedding, payload, step)
3. only after export succeeds, update the same private graph entity
```

Thus an export failure prevents the core patch.  A successful export followed
by a core patch failure leaves the deep record in place; legacy has no
compensating delete.  D6 neither changes nor emulates that behavior.

```text
DEEP_EXPORT_BEFORE_CORE_PATCH = YES                 # legacy characterization
DEEP_EXPORT_FAILURE_PREVENTS_CORE_PATCH = PASS      # legacy characterization
CORE_PATCH_FAILURE_DOES_NOT_COMPENSATE_DEEP = PASS  # legacy characterization
```

## External deep-store identity and retry gap

Deep memory remains external.  The store writes JSONL under the private-agent
path and embeds only `eid` as the primary in-memory/retrieval identity.  Its
embedding cache also keeps a latest vector by bare EID.  It preserves selected
payload metadata when available, but the deep-record format does not carry a
required source legacy namespace, semantic-scope ID, or source-object/revision
identity.  `export()` is append-only and has no idempotency key, export receipt,
or duplicate-detection contract.

Consequently the current external format cannot truthfully support a future
shared-source deep export, nor can it distinguish replay from duplicate export
after a lost response.  D6 does not write a misleading bare shared EID into a
private store.

| Failure/retry point | D6 disposition |
| --- | --- |
| Short-path core response lost | Blocked: no exact typed compression successor exists. |
| Deep export response lost | Blocked: external export has no idempotency/deduplication receipt. |
| Deep export succeeds; core patch response lost | Legacy leaves the deep record; enabled native replay is blocked. |
| Core successor retry | Blocked with the absent exact typed successor. |

```text
DEEP_MEMORY_STORE_REMAINS_EXTERNAL = YES
DEEP_RECORD_SCOPE_QUALIFIED_SOURCE_IDENTITY = NO
DEEP_EXPORT_RETRY = BLOCKED
```

## Vector consequence

Deep export alone does not mutate a core representation and therefore does not
invalidate a core vector.  A hypothetical core compression successor would
need an explicit representation-continuity decision; D6 does not assume that
every payload successor dirties the vector lane.  The qualified disabled path
does neither operation.

```text
COMPRESSION_VECTOR_LANE_EFFECT = NONE_FOR_QUALIFIED_DISABLED_NOOP
ENABLED_COMPRESSION_VECTOR_POLICY = BLOCKED_WITH_ENABLED_PATH
```

## Verification and retained posture

`tests/test_substrate_native_shared_compression_deep_memory.py` proves that
the D6 adapter makes no native connection or external compression-owner read,
leaves all relevant core/representation/operation counts unchanged, covers a
fresh source and `NO_WRITE`, rejects an enabled owner at preparation, rejects
an owner that becomes enabled before a run, and rejects profile/consumer
composition or attempts to claim enabled compression/deep export.

```text
SHADOW_LEGACY_MEMORY_STATE = NONE
KERNEL_FILES_CHANGED = 0

PUBLIC_INGEST_BACKEND = LEGACY
PRODUCTION_SELECTOR_ADDED = NO
NATIVE_ACTIVE = NO
DUAL_WRITE = NO
DUAL_READ = NO
CUTOVER_OPENED = NO
```
