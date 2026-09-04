# TORMENT Memory Substrate — Phase 9D I4C

## Conflict persistence parity for the bounded private native-public route

**Status:** uncommitted qualification artifact. This is not a production
activation, a `ConflictRegistry` migration, a shared-route qualification, or a
retirement decision.

**Frozen implementation base:** `d15a065f5d6c59e126f9df33ec79bc028c9df861`.

```text
I4C_SCOPE = PRIVATE_NATIVE_PUBLIC_ONLY
CONFLICT_READ_PARITY = FROZEN_PRESERVED
CONFLICT_CANDIDATE_ACCESS_DEPENDENCY = FROZEN_I3B_NATIVE_READ_PARITY
CONFLICT_MATHEMATICS_CHANGE = NO
QUERY_ORDERING_CHANGE = NO
EXACTLY_ONCE_CLAIM = NO
SHARED_I4C_PARITY = NOT_CLAIMED
SHARED_PRECOMMIT_EXTERNAL_OWNER_RESTORATION_REQUIRED = YES
CONFLICT_REGISTRY_MIGRATION_TO_SQLITE = NO
RETIREMENT_ALLOWED = NO
REAL_PRODUCTION_ACTIVATION = NOT_AUTHORIZED
```

## Archaeology findings

### Qualified reader contract — preserved

The existing query owner remains `TormentFabric._build_conflict_map` and the
existing score/explain composition. For each queried domain it reads open
records from the external registry, bounded by the existing limit of 500. A
current-origin record is keyed only by its scope qualifier and EID:

```text
private -> ("private", origin_agent_id, eid_a|eid_b)
shared  -> ("shared", origin_domain_id, eid_a|eid_b)
```

Legacy unqualified records remain listable but are deliberately absent from
this qualified lookup. A private-origin record cannot tag another agent or a
shared hit. The frozen query score path continues to apply the open-conflict
penalty only to a canonical shared hit; I4C does not change that conditional,
the conflict score, hit ordering, ranking, or explain shape.

### Candidate access boundary — qualified native transport

```text
CONFLICT_HEURISTIC_OWNER = LEGACY_UNCHANGED
CONFLICT_CANDIDATE_ACCESS = NativePostWriteMemoryAccess under frozen I3B read parity
```

The legacy contradiction method remains the cognitive decision and writer law.
I4C neither replaces nor redefines it. Its candidate memories are supplied by
`NativePostWriteMemoryAccess`, the qualified native read transport built on
the frozen I3B current-candidate contract, rather than by direct
`MemoryGraph.search`. I4C therefore depends on I3B candidate-read parity and
introduces no candidate-filtering rule of its own.

### Legacy writer and durable owner — preserved

`LegacyFabricPostWriteAdapter._run_contradiction_surface` is the exact writer
contract. On a created private core memory with an EID, it uses the qualified
post-write memory reader to search the current embedding lane with `top_k=3`
and the existing agent filter. It preserves every existing gate:

```text
ZERO_NORM -> return
eid <= 0 or self -> skip
non-core candidate -> skip
existing _detect_canon_conflict -> unchanged
first detected conflict -> append then break
```

The durable owner remains `ConflictRegistry`, not native SQLite. It appends a
new UUID-bearing open record to
`workspaces/<workspace>/domains/<domain>/conflicts.jsonl`; its separate
decision stream remains `conflict_events.jsonl`. The I4C private writer stamps
`origin_scope="private"`, the current `origin_agent_id`, and no
`origin_domain_id`, matching the frozen reader identity contract.

### Outcome gates and post-canonical order

The public executor withholds every post-write adapter from a structured
canonical flush failure. A true split therefore reaches I4C only after the
native source is durable and route-witness currentness has been validated.

```text
canonical flush failure -> no post-write witness; no conflict write
ordinary NO_WRITE     -> no native source; no conflict write
REINFORCED_EXISTING   -> no created-memory consumer; no conflict write
CREATED_NEW/private/core/EID -> eligible contradiction surface
```

Ordinary private `CREATED_NEW` already used the retained contradiction surface
in the qualified core staging route. The missing writer path was the I4B-2
private true-split branch: its special dispatch ran only M1/M2 maintenance and
bounded anchors, so it bypassed the first legacy created-memory consumer.

I4C adds exactly that retained call after native currentness/witness validation
and before the I4B-2 motif tail:

```text
canonical native source
  -> I4C ConflictRegistry contradiction surface (fail soft)
  -> I4B-2 motif maintenance / bounded anchors (independent fail-soft slots)
```

SRG, Hivemind, world, Character, checkpoint, compression/deep, proposal, and
bridge consumers remain outside this branch. Shared contexts remain on their
separately qualified dispatch and do not enter this private composition.

### Failure, replay, and restart disposition

The retained contradiction surface has its own broad catch: an external
registry/search/detection failure is debug-suppressed and leaves the canonical
memory durable. It also does not suppress the later I4B-2 motif slot; those
are independent failure boundaries.

There is no conflict operation key, outbox, global transaction, or dedupe
claim. A public receipt can recover a durable native source after an incomplete
post-write attempt, but the conflict owner may be re-entered. A later replay
can therefore omit a conflict after a prior suppressed failure or append a
second qualifying external record after a partial success. This is the
existing owner disposition, not exactly-once parity.

## Implementation and evidence

Only the private true-split post-write seam changes:

```text
NativeFabricPostWriteAdapter._run_i4b2_true_split_tail
  -> require qualified conflict consumer
  -> LegacyFabricPostWriteAdapter._run_contradiction_surface(context)
  -> existing I4B-2 maintenance/anchor tail
```

No conflict heuristic, reader, registry schema, query math, query ordering, or
shared route was changed.

Focused qualification evidence, executed with `conda activate torment`:

```text
tests/test_substrate_native_post_write_runtime.py
tests/test_p9d_i4b1f_public_outcome_parity.py
tests/test_conflict_origin_scope.py
tests/test_p9d_i3b_query_read_parity.py

56 passed
```

The true-split fixture proves the retained private writer runs before the motif
tail, stamps the qualified private origin, excludes all other broad post-write
consumers, and leaves motif maintenance reachable after a forced registry
failure. Existing outcome tests preserve the no-write, reinforcement, and
canonical-failure fences; existing origin and I3B tests preserve reader
isolation and query behavior.

## Bounded verdict

```text
I4C_TRUE_SPLIT_ARCHAEOLOGY = COMPLETE
I4C_TRUE_SPLIT_WRITER_READER_RECONCILIATION = LAWFUL_PRIVATE_SCOPE
P9D_I4C_TRUE_SPLIT_CONFLICT_PERSISTENCE_PARITY = PASS_BOUNDED_PRIVATE_NATIVE_PUBLIC_SCOPE
CONFLICT_READ_PARITY = FROZEN_PRESERVED
CONFLICT_WRITER_PARITY = PASS_PRIVATE_TRUE_SPLIT_NATIVE_PUBLIC_SCOPE
CONFLICT_READER_WRITER_CONTRACT = QUALIFIED_TRUE_SPLIT_SCOPE
CONFLICT_POSTCOMMIT_ORDER_PARITY = PASS
CONFLICT_FAILURE_DISPOSITION = PASS
CONFLICT_RESTART_PARITY = PASS
CONFLICT_REPLAY_MODEL = QUALIFIED_NO_EXACTLY_ONCE_DEDUP_CLAIM
CONFLICT_EXTERNAL_OWNER = PRESERVED_LEGACY_JSONL
CONFLICT_CANDIDATE_ACCESS_DEPENDENCY = FROZEN_I3B_NATIVE_READ_PARITY
SHARED_I4C_PARITY = NOT_CLAIMED
CONFLICT_FORMULA_CHANGES = 0
CONFLICT_QUERY_ORDER_CHANGES = 0
TORMENT_MATHEMATICS_PRESERVED = YES
RETIREMENT_ALLOWED = NO
REAL_PRODUCTION_ACTIVATION = NOT_AUTHORIZED
I4C_READY_TO_FREEZE = YES
I4D_STARTED = NO
```

## I4F-A adversarial amendment — broad-private writer correction

The original I4C true-split qualification above remains frozen and valid: its
retained external `ConflictRegistry` call precedes the true-split motif tail,
and its reader, mathematics, ordering, schema, failure, replay, and shared
non-claim are unchanged. During I4F-A review, however, the historic statement
that ordinary broad-private `CREATED_NEW` already reached that writer was
falsified.

Before I4F-A, the public workspace view provided shared read-only conflict
registries. The broad-private chosen domain could not obtain a writable
private registry from that map; the initial I4F narrow workspace then omitted
`conflicts` altogether. Consequently, the otherwise retained legacy
contradiction surface was fail-soft but produced zero ordinary broad-private
conflict rows. That was a writer-binding gap, not a change to the frozen
reader contract or conflict heuristic.

I4F-A corrects only this bounded binding. Its private external workspace maps
the prepared agent's admitted private motif domain to the existing writable
`ConflictRegistry`, and maps no shared domain. The existing legacy
contradiction method now receives that registry through its normal workspace
lookup and appends the existing private-origin JSONL record. The frozen
`_ReadOnlyConflictRegistry` query reader was not changed or replaced, and its
qualified native query composition does not currently include this private
conflict domain. The durable external evidence is therefore lawful write-side
parity, not a qualified broad-private reader/writer roundtrip.

```text
I4C_TRUE_SPLIT_CONFLICT_PREFIX = FROZEN_PRESERVED
I4C_TRUE_SPLIT_READER_WRITER_CONTRACT = FROZEN_PRESERVED
I4C_BROAD_PRIVATE_PREEXISTING_WRITER_ASSUMPTION = FALSIFIED_DURING_I4F_A_REVIEW
I4C_BROAD_PRIVATE_CONFLICT_WRITER = PASS_WRITE_SIDE_ONLY
I4C_BROAD_PRIVATE_CONFLICT_EXTERNAL_OWNER = QUALIFIED_PRESERVED
I4C_BROAD_PRIVATE_CONFLICT_READ_ROUNDTRIP = NOT_YET_QUALIFIED
I4C_BROAD_PRIVATE_CONFLICT_SYSTEM_PARITY = NOT_YET_QUALIFIED
I4C_BROAD_PRIVATE_CONFLICT_OWNER = CORRECTED_I4F_A_EXTERNAL_CONFLICTREGISTRY
CONFLICT_MATHEMATICS_CHANGE = NO
CONFLICT_QUERY_READER_CHANGE = NO
CONFLICT_QUERY_ORDERING_CHANGE = NO
CONFLICT_REGISTRY_SCHEMA_CHANGE = NO
CONFLICT_EXTERNAL_OWNER = PRESERVED_LEGACY_JSONL
CONFLICT_FAILURE_DISPOSITION = RETAINED_FAIL_SOFT
CONFLICT_REPLAY_MODEL = RETAINED_APPEND_NO_EXACTLY_ONCE_CLAIM
SHARED_I4C_PARITY = NOT_CLAIMED
```

This amendment does not re-qualify the true-split work by association. It
records the separately corrected ordinary broad-private writer binding. The
remaining query-domain-composition gap is a named prerequisite, not a reason
to alter the frozen reader in this proposal/bridge slice.

```text
I4C_R1_BROAD_PRIVATE_CONFLICT_READ_ROUNDTRIP = OPEN
I4C_R1_REQUIRED_BEFORE_I4G_FINAL_FREEZE = YES
```

I4C-R1 must establish this unchanged chain in its own archaeology and
qualification work:

```text
broad-private external ConflictRegistry evidence
  -> qualified native conflict reader
  -> existing conflict scoring / trace semantics
```

It must not change the conflict heuristic, record schema, query scoring
formula, query ordering, or origin semantics.
