# TORMENT Memory Substrate — Phase 9D I3C

## Query/external composition parity

**Status:** qualified offline over synthetic SQLite cores and isolated legacy
graphs. This is an uncommitted review artifact. It authorizes neither a real
root nor service/provider contact, re-embedding, native cutover, or legacy
reader retirement.

## 0. Scope and preserved owner

```text
MAIN_TORMENT_QUERY_COGNITION_OWNER =
    ThinkingController MemoryPlan policy + TormentFabric.query

ONE_QUERY_COGNITION_IMPLEMENTATION = PRESERVED
QUERY_FORMULA_CHANGES_REQUIRED = NO
TORMENT_MATHEMATICS_PRESERVED = YES
REAL_ROOT_CONTACT = NO
SERVICE_START = NO
PROVIDER_CONTACT = NO
REAL_REEMBEDDING = NO
REAL_PRODUCTION_ACTIVATION = NOT_AUTHORIZED
```

I3C is a composition characterization. It leaves scoring, continuity,
ordering, domain routing, motif mathematics, Character equations, and SRG
multiplier mathematics in their existing owners. It does not migrate general
post-write cognition; that remains I4.

I3CF makes documentary/evidence corrections only:

```text
I3CF_PRODUCTION_BEHAVIOR_CHANGES = 0
I3CF_QUERY_COGNITION_CHANGES = 0
I3CF_POST_WRITE_COGNITION_CHANGES = 0
I3CF_MATHEMATICS_CHANGES = 0
```

I3C itself has one explicitly bounded historical behavior repair, documented
in §4.2. It is an SRG error-handler defect repair, not a scoring, query-formula,
or SRG-mathematics change.

The corrected historical boundary is retained:

```text
BRAINVISION_FILES_READ = NOT_CERTIFIABLE_AS_ZERO
BRAINVISION_SEARCH_SNIPPETS_EXPOSED = YES
BRAINVISION_DOCUMENTATION_MENTION_OPENED = YES
BRAINVISION_CODE_OPENED = NO
BRAINVISION_CODE_INSPECTED = NO
BRAINVISION_FILES_TOUCHED = 0
BRAINVISION_INFORMATION_USED = NO
SECOND_REPOSITORY_COGNITIVE_FUNCTION_INSPECTED = NO
```

## 1. Preservation matrix

`TORMENT_MEMORY_SUBSTRATE_FUNCTIONALITY_PRESERVATION_MATRIX_v0.1.md` is the
living cross-slice inventory and the bounded functionality-preservation
denominator. It records current semantic and durable owners, native adapters,
bounded parity evidence, composition gates, and a frozen
`RETIREMENT_ALLOWED = NO` for every row. Its 72 source-live capabilities cover
the public/service operation surface, the main query graph, and the main
ingest/post-write graph; every capability maps to a matrix row.

The matrix makes the central preservation rule explicit:

```text
LEGACY_FUNCTIONALITY = REFERENCE
NATIVE_GAP = ACTIVATION_BLOCKER
NATIVE_GAP != PERMISSION_TO_REMOVE_LEGACY_BEHAVIOR
MATRIX_ROW_ABSENT = RETIREMENT_FORBIDDEN
UNMAPPED_LIVE_CAPABILITY = ACTIVATION_BLOCKING
```

It is intentionally conservative. `OPEN`, `PARTIAL`, `BLOCKING`, and `NOT YET
QUALIFIED` are not aliases for a hidden pass.

## 2. I3B follow-up fixtures

### 2.1 Non-contiguous EID ordering

The I3C fixture creates source EIDs `0, 1, 2, 3`. EID `2` has only a pending
representation and is therefore not a candidate; EID `1` receives its current
R2 after EID `3` already exists. The exact vector candidate sequence is:

```text
LEGACY_EID_ROWS = [0, 1, 3]
NATIVE_EID_ROWS = [0, 1, 3]
NATIVE_SNAPSHOT_ROWS = [0, 1, 3]
MIDDLE_R2_REINFORCEMENT_COUNT = 9
```

The result proves numeric EID ordering is not a coincidental source-adoption
or R2-update order. It does not introduce an EID ranking rule; the existing
`argsort`/stable result behavior remains the owner.

### 2.2 First native snapshot failure

A first-read `_build_snapshot` failure yields `_ensure_snapshot() -> None`,
then `NativeVectorReadConsistencyRefused`, then
`NativeQuerySnapshotReadRefused`. The public wrapper maps the existing native
read-refusal family to `NativePublicOperationRefused`.

```text
FIRST_STALE_SNAPSHOT_DISPOSITION = PASS
VALID_EMPTY_LANE != UNREBUILDABLE_NATIVE_SNAPSHOT
```

### 2.3 Malformed vector disposition

The representations are not semantically identical in malformed state:

```text
LEGACY_DIRECT_NAN_CACHE_INJECTION = candidate with NaN raw score
LEGACY_SORT_DISPOSITION = finite rows precede the NaN row in this fixture
NATIVE_NONFINITE_QUALIFIED_VECTOR = candidate rebuild refusal
NATIVE_PUBLIC_RESULT = qualified read refusal, not an empty lane
```

Native has an explicit finite-float32 qualification law. I3C preserves the
asymmetry instead of normalizing legacy behavior or weakening native proof.

```text
MALFORMED_VECTOR_DISPOSITION = LAWFUL_FAIL_CLOSED_ASYMMETRY
MALFORMED_VECTOR_QUERY_PARITY = NOT_APPLICABLE_UNDER_QUALIFIED_ADMISSION
MALFORMED_LEGACY_REPRESENTATION_GATE = PRE_ACTIVATION
```

A legacy non-finite representation cannot be natively admitted unchanged. It
must be normalized, dispositioned, or excluded under a qualified migration
policy; I3C does not reproduce legacy NaN/Inf query behavior.

### 2.4 Zero-budget lane verdict

When a MemoryPlan gives a lane zero budget, the corresponding lane search is
not called. Therefore no snapshot currentness claim is made for that unused
lane, including if its next rebuild would refuse.

```text
NO_LANE_READ = NO_LANE_CONSISTENCY_CLAIM_REQUIRED
ZERO_BUDGET_STALE_SNAPSHOT = NOT_PROBED
```

This preserves the current `top_k <= 0` behavior; I3C does not force an
unused native lane to rebuild solely to discover stale state.

### 2.5 Main query cognition and query-side bridge scope

The established main-query owner is not a storage adapter:

```text
MAIN_QUERY_COGNITION_OWNER =
    ThinkingController MemoryPlan policy
    +
    TormentFabric.query
```

`ThinkingController` supplies lane budgets and weights, bounded lane
allocation, and deep-lane interaction. `TormentFabric.query` retains the
retrieval, merge, scoring, and result-assembly owner. Native storage supplies
qualified facts; it must not become the MemoryPlan owner.

FILTER-A is a separate active query-semantic chokepoint. The existing
governance path calls `filter_llm_facing` before LLM-facing context is used,
returns both `excluded` and `filter_excluded`, and records
`_core_hits_in_count`. I3C neither replaces that path with native storage nor
changes its filtering semantics.

Bridge peek is query-side retrieval, not bridge suggestion mutation. When
requested, it obeys `bridge_peek_requires_approval`; otherwise a bridge must
be approved or meet the existing confidence threshold. Retrieved hits are
marked `via_bridge`. The independently owned post-write bridge-suggestion
route remains an I4 capability.

## 3. Character external-owner boundary

`CharacterStore` remains the external durable owner. I3C distinguishes the
internal causes without changing their externally visible behavior:

| Internal condition | Existing `TormentFabric.query` result |
|---|---|
| Referenced seed/state is absent | No `character_context`; base query survives |
| `CharacterStore.load_seed` raises | No `character_context`; base query survives |

The broad fail-soft boundary intentionally maps both facts to the same public
absence. Distinguishing them in output would require a query-cognition change,
which I3C does not make.

```text
CHARACTER_QUERY_FAILURE_DISPOSITION = MAPPED_TO_OPTIONAL_CONTEXT_ABSENCE
CHARACTER_CONTEXT_ABSENCE = NOT_A_HEALTH_SIGNAL
CHARACTER_QUERY_PARITY = PASS
CHARACTER_SEED_DRIFT_GRAVITY_WRITE_COMPOSITION = BLOCKED_PENDING_I4
CHARACTER_STORE_MIGRATION_TO_SQLITE = NOT_AUTHORIZED
```

## 4. SRG read, refusal, and mutation characterization

### 4.1 Read and explain

The all-modifier fixture proves the existing scoring/explain multipliers are
unchanged under native-qualified reads:

```text
SAME_BAND = 1.08
CRYSTAL = 1.05
HEARTBEAT_A = 1.03
TOTAL = 1.08 * 1.05 * 1.03
```

### 4.2 Native refusal propagation

The native effective-SRG read had been inside a broad `except Exception` in
Fabric. I3C adds a narrow re-raise for the established
`NativeQueryReadRefused` contract before the retained generic fail-soft catch.
This makes SRG read consistency refusal fail closed: a deliberate qualified
currentness refusal no longer silently removes score modifiers.

```text
SRG_NATIVE_REFUSAL_SWALLOWED = NO
GENUINE_OPTIONAL_ABSENCE = EXISTING_LAWFUL_DISPOSITION
DELIBERATE_NATIVE_READ_REFUSAL = PROPAGATES
SRG_READ_CONSISTENCY_REFUSAL = FAIL_CLOSED
SRG_OVERLAY_WRITE_REFUSAL = CURRENTLY_FAIL_SOFT
```

I3C intentionally fixes a latent legacy/native shared defect in the SRG error
handler. Before the change, evolution failure on the first breathing-eligible
hit could raise `UnboundLocalError` and terminate the query; on later hits the
diagnostic could name the previous memory's EID. I3C hoists `_hit_eid` before
the guarded evolution so the already-written fail-soft intent actually
executes. This is an observable behavior change, justified as an error-handler
defect repair. It changes neither query mathematics nor SRG mathematics.

```text
SRG_ERROR_HANDLER_LATENT_DEFECT_FIXED = YES
LEGACY_OBSERVABLE_BEHAVIOR_CHANGED = YES_ERROR_HANDLER_REPAIR
CHANGE_CLASS = ERROR_HANDLER_DEFECT_REPAIR
QUERY_MATHEMATICS_CHANGED = NO
SRG_MATHEMATICS_CHANGED = NO
```

The current fail-soft overlay-write refusal is permitted only while
`SRG_QUERY_WRITE_COMPOSITION = BLOCKED_PENDING_I4`. I4 must disposition SRG
overlay-write refusal before authorizing a write route.

### 4.3 Legacy breathing facts

For a complete synthetic nested SRG payload, legacy query:

1. mutates the live target entity;
2. exposes that top-level state to the next same-process query for scoring;
3. still evolves from the unchanged nested input on each query, so the stored
   state does not receive a second step merely from the second query;
4. loses the query-only mutation after restart when no later target write
   occurs;
5. also loses it when an unrelated entity is later created/flushed; and
6. serializes it when a later ordinary update writes that same target entity.

The multi-workspace legacy fixture has colliding local EIDs but mutating
`alpha / aria` does not change `grove / aria`.

```text
LEGACY_SRG_BREATHING = LIVE_PAYLOAD_MUTATION
RESTART_WITHOUT_SAME_ENTITY_WRITE = LOST
UNRELATED_ENTITY_WRITE_OR_FLUSH = DOES_NOT_PERSIST_IT
SAME_ENTITY_LATER_WRITE = SERIALIZES_THE_EVOLVED_STATE
```

### 4.4 Native breathing facts

For the same full state shape, native query evolves a process-local overlay
under the exact `(core_id, legacy_source_namespace_id, eid, revision_id)`
witness. A second native read in the same process observes the overlay. A new
`NativeQualifiedQueryReadModel` with a new process state does not.

The collision fixture shares one `NativeSRGProcessState` across `orchard /
aria / eid=0` and `grove / aria / eid=0`; independent source namespaces keep
their overlays separate.

```text
ONE_REQUEST_COGNITIVE_WORKSPACE = YES
SRG_MULTI_WORKSPACE_ISOLATION = PASS
SRG_QUERY_READ_PARITY = PASS
SRG_SAME_PROCESS_MUTATION_PARITY = PASS_WITHIN_HISTORICAL_NESTED_GATE
SRG_RESTART_PARITY = BLOCKED_PENDING_I4
SRG_QUERY_WRITE_COMPOSITION_PARITY = BLOCKED_PENDING_I4
CURRENT_OVERLAY = PROCESS_LOCAL_ONLY
```

The restart verdict is deliberately not collapsed into the no-write case:
legacy can carry its query mutation across a restart after a later write of
the same entity, while native query creates no durable successor. I3C does not
invent that successor path inside query.

## 5. Motif live insertion order

The I3B motif pass applies to persisted/recovered state. I3C adds the missing
legacy live-state witness:

```text
PERSISTED_RELOAD_ORDER = lexical motif ID order
PERSISTED_RECOVERED_LEGACY_MOTIF_ORDER = LEXICAL
LIVE_POST_LOAD_NEW_MOTIFS = append / creation order
ACTIVE_AND_CENTROID_LOOPS = consume that live dict order
```

Native query currently reconstructs durable motif aliases and has no I4 native
post-write path that can produce/retain this live insertion witness. I3C
therefore does not impose a legacy sort or invent a new native tie policy.

```text
MOTIF_LIVE_INSERTION_ORDER_PARITY = BLOCKED_PENDING_I4_ORDER_WITNESS
```

I4 must preserve a truthful, explicit live-order witness before a native
post-write path participates in the same active/centroid behavior.

## 6. External composition dispositions retained

```text
CONFLICT_READ_PARITY = PASS
CONFLICT_SYSTEM_PARITY = BLOCKED_PENDING_I4

CHARACTER_QUERY_PARITY = PASS
CHARACTER_WRITE_COMPOSITION = BLOCKED_PENDING_I4

COLLECTIVE_QUERY_NATIVE_DISPOSITION = REFUSE_WHEN_APPLICABLE
COLLECTIVE_QUERY_ACTIVATION_GATE = OPEN

ARCHIVE_RECALL_NATIVE_DISPOSITION =
    REFUSE_UNTIL_PARITY_OR_EXPLICIT_INAPPLICABILITY
ARCHIVE_RETRIEVAL_COUNT_WRITE = COMPOSITION_GATE

REFERENCE_CLASS_QUERY_DISPOSITION =
    PRESERVE_EXISTING_NATIVE_PARITY_READY_CLASSIFICATION
```

Reference, environment, baton, and closure are not blanket-refused merely
because their names are reference-like. For ordinary query-memory
classification they remain native-parity-ready because `_NON_DEFAULT_CLASSES`
excludes them from MemoryGraph query cognition. A public surface that writes
or materializes one of them remains a separately classified route.

Deep budget remains structurally unequal to the qualified native core-staging
profile. Equality fixtures use no deep budget; a native query with enabled
deep retrieval retains its explicit refusal. The repository source default is
not evidence of a real production configuration.

```text
DEEP_RETRIEVAL_NATIVE_DISPOSITION = REFUSE_WHEN_APPLICABLE_UNTIL_QUALIFIED
DEEP_RETRIEVAL_PROFILE_GATE = OPEN_PRE_ACTIVATION
```

## 7. Focused qualification inventory

`tests/test_p9d_i3c_query_external_composition_parity.py` covers:

- non-contiguous EID ordering with post-higher-EID reinforcement;
- first native snapshot rebuild refusal through the public wrapper;
- zero-budget non-read semantics;
- malformed-vector legacy/native dispositions;
- SRG multi-workspace collision isolation and all explain modifiers;
- native SRG refusal propagation;
- Character absent-versus-unreadable fail-soft mapping;
- legacy same-process/restart/later-write SRG behavior and workspace scope;
- native overlay same-process-only behavior; and
- legacy live motif insertion ordering.

The documented regression set is rerun separately before review. It uses a
writable pytest base outside the repository and contains no real-root,
service, or provider contact.

## 8. I3C verdict

```text
P9D_I3C_QUERY_EXTERNAL_COMPOSITION = PASS
I3C_DOCUMENTARY_CORRECTIONS = PASS
ONE_QUERY_COGNITION_IMPLEMENTATION = PRESERVED
NON_CONTIGUOUS_EID_ORDER_PARITY = PASS
FIRST_STALE_SNAPSHOT_DISPOSITION = PASS
MALFORMED_VECTOR_DISPOSITION = LAWFUL_FAIL_CLOSED_ASYMMETRY
MALFORMED_VECTOR_QUERY_PARITY = NOT_APPLICABLE_UNDER_QUALIFIED_ADMISSION
MALFORMED_LEGACY_REPRESENTATION_GATE = PRE_ACTIVATION
CHARACTER_QUERY_FAILURE_DISPOSITION = MAPPED
CHARACTER_CONTEXT_ABSENCE = NOT_A_HEALTH_SIGNAL
SRG_NATIVE_REFUSAL_SWALLOWED = NO
SRG_ERROR_HANDLER_LATENT_DEFECT_FIXED = YES
LEGACY_OBSERVABLE_BEHAVIOR_CHANGED = YES_ERROR_HANDLER_REPAIR
SRG_QUERY_READ_PARITY = PASS
SRG_SAME_PROCESS_MUTATION_PARITY = PASS_WITHIN_HISTORICAL_NESTED_GATE
SRG_RESTART_PARITY = BLOCKED_PENDING_I4
SRG_QUERY_WRITE_COMPOSITION_PARITY = BLOCKED_PENDING_I4
SRG_MULTI_WORKSPACE_ISOLATION = PASS
MOTIF_LIVE_INSERTION_ORDER_PARITY = BLOCKED_PENDING_I4_ORDER_WITNESS
CONFLICT_READ_PARITY = PASS
CONFLICT_SYSTEM_PARITY = BLOCKED_PENDING_I4
CHARACTER_QUERY_PARITY = PASS
CHARACTER_WRITE_COMPOSITION = BLOCKED_PENDING_I4
COLLECTIVE_QUERY_NATIVE_DISPOSITION = REFUSE_WHEN_APPLICABLE
ARCHIVE_RECALL_NATIVE_DISPOSITION = REFUSE_UNTIL_PARITY_OR_EXPLICIT_INAPPLICABILITY
REFERENCE_CLASS_QUERY_DISPOSITION = PRESERVE_EXISTING_NATIVE_PARITY_READY_CLASSIFICATION
FUNCTIONALITY_PRESERVATION_MATRIX = QUALIFIED_BASELINE
FUNCTIONALITY_MATRIX_DENOMINATOR = ESTABLISHED
UNMAPPED_LIVE_CAPABILITIES = 0
DEEP_MEMORY_SPIRIT_RETURN_ROW = PRESENT
GOVERNANCE_FILTER_A_ROW = PRESENT
THINKINGCONTROLLER_MEMORYPLAN_ROW = PRESENT
BRIDGE_PEEK_ROW = PRESENT
LEGACY_QUERY_READER_RETIREMENT = NOT_AUTHORIZED
QUERY_FORMULA_CHANGES_REQUIRED = NO
TORMENT_MATHEMATICS_PRESERVED = YES
REAL_PRODUCTION_ACTIVATION = NOT_AUTHORIZED
```

## 9. I4 requirements carried forward

The complete `I4_REQUIRED_PARITY_ROWS` list is frozen in the matrix
denominator. In particular, I4 must address input write gate/provenance,
memory creation, reinforcement, motif attach/create and live insertion order,
conflict persistence, SRG post-write state and overlay-write refusal,
Character seed/drift/gravity, role/affect, derived memory, world/trajectory,
checkpoint, compression/deep export, Hivemind, shared ingest, proposals,
bridge suggestions, archive count/document lifecycle, index rebuild,
promotion, and reference/environment/baton/closure lifecycle. No native
post-write activation can selectively omit an unmapped capability.

No legacy query reader, external owner, or historical behavior is retired by
this receipt.
