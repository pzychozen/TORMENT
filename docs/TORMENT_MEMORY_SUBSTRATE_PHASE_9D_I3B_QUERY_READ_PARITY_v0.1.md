# TORMENT Memory Substrate — Phase 9D I3B

## Native query-read parity and observable-order preservation

**Status:** qualified offline over synthetic SQLite cores and pre-existing
external fixture state. This receipt is neither a real-root observation nor an
activation authorization.

## 0. Authority and scope

```text
MAIN_TORMENT_COGNITION_OWNER =
    ThinkingController MemoryPlan policy + TormentFabric.query

ONE_ACTIVE_TORMENT_QUERY_COGNITION_IMPLEMENTATION = YES
QUERY_FORMULA_CHANGES_REQUIRED = NO
REAL_ROOT_CONTACT = NO
SERVICE_START = NO
PROVIDER_CONTACT = NO
REAL_PRODUCTION_ACTIVATION = NOT_AUTHORIZED
```

`NativeQualifiedQueryReadModel` remains the qualified storage/read port. It
may validate lane identity, reconstruct a candidate projection, expose durable
ordering witnesses, expose current motif geometry, and report read
consistency. It does not own score meaning, continuity policy, conflict
penalty, SRG multiplier meaning, Character semantics, final ranking, or
top-level truncation.

Every use of query cognition, cognition implementation, cognition owner, and
cognition convergence here means **MAIN TORMENT COGNITION**. No implementation
phase in this receipt imports, calls, replaces, merges with, or retires the
unrelated repository cognitive function.

## 1. Snapshot disposition

The native vector cache previously represented two materially different states
as an empty list: a successfully read lane without matches and a cache that
could not prove currentness after a rebuild or selected-row race.

I3B adds a narrow, non-retrying boundary:

```text
VALID_EMPTY_LANE = ()
STALE_OR_UNQUALIFIED_NATIVE_SNAPSHOT =
    NativeVectorReadConsistencyRefused
READ_MODEL_TRANSLATION =
    NativeQuerySnapshotReadRefused
```

`NativeMemoryVectorRuntime` raises the lower refusal when no qualified snapshot
can be rebuilt, or when selected vectors no longer validate against current
payload rows. `_NativeQualifiedQueryLane` translates that refusal to the
existing `NativeQueryReadRefused` family. Fabric and the native public wrapper
therefore retain their established fail-closed refusal path. No automatic retry
and no query-scoring change was introduced.

Blank queries, successfully built zero-vector lanes, and ordinary filters with
zero matches remain valid empty results. A selected-row currentness race is now
positively detectable as `concurrent-currentness-change`.

## 2. Observable ordering census

| Surface | Legacy source of order | Native source of order | Parity result |
|---|---|---|---|
| Vector candidate rows, private and shared | `MemoryGraph._rebuild_matrix()` sorts qualified embedding EIDs ascending before its shared `argsort`/`argpartition` law. | `NativeMemoryVectorRuntime._build_snapshot()` sorts matrix rows by the same canonical EID. Runtime ordinals remain durable source witnesses, not a replacement ranking rule. | PASS |
| Private/shared merge | `TormentFabric.query`: private lane, then selected shared domains in the caller's order, then any bridge-peek lanes. | Same existing query owner and helper sequence. | PASS |
| Domain selection | Workspace declared/shared-graph insertion order; stable score sort preserves exact ties before top-two truncation. | Recovered descriptor scope order is explicit; `NativeQualifiedQueryReadModel.domain_ids()` returns it rather than SQL incidental order. | PASS |
| Motif iteration and domain centroid reduction | Persisted `MotifRegistry.save()` uses `sort_keys=True`; a restarted registry iterates the resulting lexical motif-ID object order. | Scoped unique `MOTIF_ID` aliases are read in lexical order before weighted float reduction. | PASS for the offline persisted/recovered contract |
| Active motif full ties | Python stable sort over registry iteration with `(strength + gravity, last_active_ts)`. | Same `_active_summary` law over the recovered native motif order. | PASS |
| Dominant thread | Domain encounter order, then active-motif encounter order; strict raw-strength `>` retains the first full tie. | Existing `dominant_thread` receives the same ordered active context. | PASS |
| Bridge ordering | Persisted bridge-list order, then stable confidence sort. | I3B keeps the existing bridge owner/read path; no adapter ordering is introduced. | Preserved / not reimplemented |
| Conflict IDs exposed by query | JSONL application order enters the map; stable created-time order controls `list()`. | I3B uses the existing qualified read disposition and preserves the conflict owner. | PASS |

The motif conclusion is intentionally bounded to the frozen offline recovery
contract. A transient, unsaved in-process registry insertion order is not
substituted with a new native rule. The production-shaped cutover target starts
from a persisted stopped root, for which the serialized motif-ID order is the
durable recoverable witness.

## 3. Geometry, zero-member motifs, and active context

Native `MotifRuntimeReader.domain_centroid()` retains the legacy iteration and
weight law:

```text
weight = max(1e-6, strength) * (1 + gravity_bonus)
```

The zero-member B4C fixture verifies a certified zero-member motif with a
centroid, stability, and **zero strength**. It has no synthesized member, yet
it contributes a non-zero weighted geometric centroid, has its ordinary gravity
and active-context projection, and remains available to the existing
motifless-hit fallback alignment loop. The test also verifies that native and
legacy geometry/active projections agree at target dimension 384.

Active motif ranking and dominant-thread selection are intentionally separate:

```text
ACTIVE_MOTIF_ORDER = strength + gravity_bonus, then last_active_ts
DOMINANT_THREAD = raw strength, strict first-encounter tie retention
```

I3B proves the case where a gravity-leading motif is active first while a
different raw-strength-leading motif is the dominant thread. Neither behavior
was normalized into the other.

## 4. Representation and decomposition parity

```text
I3_QUERY_PARITY_INPUT = SAME_QUALIFIED_REPRESENTATION_STATE
TARGET_QUALIFIED_LANE = st / BAAI/bge-small-en-v1.5 / 384
```

The deterministic three-dimensional fixtures exist only to make order and
component differences observable. They do not compare historical or unknown
vectors with the target lane. The certified zero-member fixture exercises the
384-dimensional target lane.

The differential explain test verifies the same public decomposition, not just
the same final score: similarity, motif alignment, continuity adjustment,
conflict penalty/status, SRG multiplier, and memory-plan lane weight are
identical when the existing query owner consumes native-qualified reads.

Conflict **read** parity is qualified for equivalent evidence. Conflict system
write/activation parity remains blocked:

```text
CONFLICT_READ_PARITY = PASS
CONFLICT_SYSTEM_PARITY = BLOCKED_PENDING_I4
```

Character seed/state reads, seed preamble/context, tiers, weighting metadata,
and drift context retain the existing external `CharacterStore` owner and the
existing A3 differential parity coverage. I3B does not migrate the store or
change Character equations.

The native effective-SRG reader remains the query-time source when no overlay
is present; the existing A3 differential coverage verifies the source used by
score/explain and the same-band, crystal, and heartbeat fields. I3B makes no
claim about SRG breathing or durable mutation:

```text
SRG_QUERY_READ_SOURCE_PARITY = PASS
SRG_QUERY_MUTATION_PARITY = OPEN_I3C_GATE
```

## 5. Workspace isolation and failure dispositions

The I3B multi-workspace fixture creates `orchard / aria` and `grove / aria`
with the same local EID and the same shared `research` domain identifier. Each
native/legacy-compatible pair returns identical query output inside its own
workspace, while `QueryMemoryIdentity` retains distinct workspace-qualified
identity. Candidate, motif, and provenance facts do not cross the workspace
boundary.

```text
ONE_REQUEST_COGNITIVE_WORKSPACE = YES
MULTI_WORKSPACE_QUERY_PARITY = PASS
```

The qualified disposition inventory is:

| Case | Disposition |
|---|---|
| Blank query, filter-empty, or successfully built zero-vector lane | Valid empty result |
| Wrong read-model workspace / absent admitted lane | Existing explicit read-model refusal (`QualifiedQueryReadModelError` / `KeyError`) |
| Query embedding dimension mismatch | Existing explicit HTTP 409 dimension refusal |
| Missing optional Character or conflict evidence | Existing optional empty/absent semantics |
| Malformed conflict evidence | Existing `NativeQueryReadRefused`; not silently downgraded |
| Stale/invalidated selected native snapshot | `NativeQuerySnapshotReadRefused`; not an empty lane |
| Stale native membership/profile witness | Existing qualified identity/currentness refusal |

## 6. Formula-duplicate inventory

| Semantic owner | Duplicate/storage-side owner | Parity test | Retirement gate | Eventual survivor |
|---|---|---|---|---|
| `MemoryGraph` cached vector normalization, selection, and decay behavior | `NativeMemoryVectorRuntime` cache projection | `test_p9d_i3_vector_normalization_and_decay_parity` | Native read qualification remains stable through I3C/I4 | Existing one query cognition owner over a qualified read port |
| DomainRouter cosine/stable-order behavior | `_rank_domains_from_read_model` consumes alternate geometry facts | `test_p9d_i3_domain_rank_order_parity` | No independent router policy may appear | Existing query owner |
| `MotifRegistry` geometry/active behavior | Native motif reader plus `_active_summary` projection | `test_p9d_i3_motif_geometry_active_order_parity`; zero-member test | Persisted-order recovery must remain provable | Existing motif decision/geometry semantics |
| `TormentFabric.query` score/explain decomposition | Native adapter supplies only qualified input facts | `test_p9d_i3_explain_decomposition_parity` | I3C/I4 write/activation gates | `TormentFabric.query` |

No duplicate is retired in I3B.

## 7. Qualification inventory

Focused I3B tests:

- `test_p9d_i3_domain_rank_order_parity`
- `test_p9d_i3_vector_normalization_and_decay_parity`
- `test_p9d_i3_motif_geometry_active_order_parity`
- `test_p9d_i3_active_motifs_vs_dominant_thread`
- `test_p9d_i3_zero_member_motif_geometry_active_and_fallback_parity`
- `test_p9d_i3_explain_decomposition_parity`
- `test_p9d_i3_effective_legacy_srg_source_matches_native_without_overlay`
- `test_p9d_i3_stale_snapshot_is_detectable_and_not_a_valid_empty`
- `test_p9d_i3_multi_workspace_same_local_ids_do_not_cross_contaminate`

I3B also reruns the I3B0 materialization fence, I3A cognition parity, I2
public/native fence, and I1/I1C root-membership regression sets. The native
query path must not create legacy workspace/agent/collective/archive/affect/
role state or retrieval counts; I3B0 remains the maintained materializer
census and its regression must remain green.

```text
P9D_I3B_FOCUSED = 9 passed
P9D_I3B0_FENCING = 10 passed
A2_A3_QUERY_MODEL_AND_COGNITION = 15 passed
P9D_I2_PUBLIC_NATIVE_FENCING = 13 passed
P9D_I1_I1C_ROOT_MEMBERSHIP = 21 passed
B4C_ZERO_MEMBER_REGRESSION = 18 passed
```

## 8. Boundary receipt and remaining gates

The previously corrected boundary is retained exactly:

```text
BRAINVISION_BOUNDARY =
    CORRECTED_AFTER_ACCIDENTAL_SEARCH_SNIPPET_EXPOSURE
BRAINVISION_FILES_READ = NOT_CERTIFIABLE_AS_ZERO
BRAINVISION_SEARCH_SNIPPETS_EXPOSED = YES
BRAINVISION_DOCUMENTATION_MENTION_OPENED = YES
BRAINVISION_CODE_OPENED = NO
BRAINVISION_CODE_INSPECTED = NO
BRAINVISION_FILES_TOUCHED = 0
BRAINVISION_INFORMATION_USED = NO
SECOND_REPOSITORY_COGNITIVE_FUNCTION_INSPECTED = NO
I3B_FINDINGS_DERIVED_FROM_BRAINVISION = NO
```

```text
P9D_I3B_QUERY_READ_PARITY = PASS
STALE_NATIVE_QUERY_SNAPSHOT = DETECTABLE
VECTOR_ORDER_PARITY = PASS
DOMAIN_ORDER_PARITY = PASS
MOTIF_FLOAT_REDUCTION_ORDER_PARITY = PASS
ZERO_MEMBER_MOTIF_QUERY_PARITY = PASS
ACTIVE_MOTIF_PARITY = PASS
DOMINANT_THREAD_PARITY = PASS
QUERY_EXPLAIN_DECOMPOSITION_PARITY = PASS
CONFLICT_READ_PARITY = PASS
CHARACTER_QUERY_PARITY = PASS
SRG_QUERY_READ_SOURCE_PARITY = PASS
MULTI_WORKSPACE_QUERY_PARITY = PASS
NATIVE_QUERY_NON_MATERIALIZATION = PASS
TORMENT_MATHEMATICS_PRESERVED = YES

CONFLICT_SYSTEM_PARITY = BLOCKED_PENDING_I4
SRG_QUERY_MUTATION_PARITY = OPEN_I3C_GATE
REAL_PRODUCTION_ACTIVATION = NOT_AUTHORIZED
```
