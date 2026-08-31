# TORMENT Memory Substrate — 7G5E0 post-D1 production applicability audit

## Result

This is a documentation-only, read-only applicability audit at
`4368b150bb7f9188f5d5d853676d94836d1e41a8`.  It freezes the completed
bounded D1 scientific result and identifies only the capabilities that still
block a safe replacement of production core-memory storage.  It neither
selects native storage nor changes a production, staging, migration, or D1
administration path.

```text
D1_ORIGINAL_FORMAL_RESULT = VALID / STORAGE_SUBSTRATE_DEFECT
D1_ORIGINAL_DIFFERENCE_COUNT = 53
D1_IDENTIFIED_DEFECT_REGRESSION_V2 = PASS / 0 remaining identified storage differences
D1_IDENTIFIED_STORAGE_DEFECTS_REMAINING = 0
SAME_INPUT_LEGACY_NATIVE_STORAGE_PARITY = YES
POST_WRITE_PASS_PRESERVED = YES
M5_PASS_PRESERVED = YES
STRUCTURAL_PASS_PRESERVED = YES
```

The original D1 result is historical scientific evidence and is unchanged.
The V2 result is narrower: the four identified 03B values were shown to be a
Fabric pre-write input recomputation mismatch, not a native durable-storage
defect.  For the same storage-facing input, legacy and native durable storage
are exact.  See `TORMENT_MEMORY_SUBSTRATE_7G5D1O_HALF_LIFE_STORAGE_INPUT_IDENTITY_v0.1.md`.

## Current production path

The currently shipped path remains wholly legacy-owned:

```text
app.py module-global TormentFabric
  -> /agent/create -> TormentFabric.create_agent
       -> IdentityStore, CharacterStore, private MemoryGraph,
          workspace MotifRegistry
  -> /agent/ingest -> TormentFabric.ingest
       -> TriOcta kernel -> legacy MemoryGraph private/shared selection
       -> search_by_embedding / update_payload or spawn_memory / flush_node
       -> LegacyMotifRuntimeAdapter.attach_or_create
       -> LegacyFabricPostWriteAdapter
  -> /agent/query and /retrieve -> TormentFabric.query
       -> private MemoryGraph.search + shared MemoryGraph.search
       -> legacy MotifRegistry and optional BridgeRegistry/deep lane
```

The decisive code facts are:

- `TormentFabric.__init__` describes an injected native binding as inert
  configuration and says no existing runtime path reads or writes it
  (`torment_service/fabric.py`).  The default binding is `None`.
- `Workspace` constructs a `MemoryGraph` for every shared domain and a legacy
  `MotifRegistry`; `create_agent` constructs a private `MemoryGraph`.
- `ingest` selects `ws.shared_graphs[chosen_domain]` for `scope == "shared"`
  and otherwise the private graph.  Its ordinary success path invokes the
  legacy motif adapter and `LegacyFabricPostWriteAdapter`.
- `query` reads the private and shared `MemoryGraph` lanes directly.  Optional
  bridge peeks select further legacy shared graphs.
- `NativeFabricRoutingCapability` is constrained to `STAGING`,
  `LEGACY_ACTIVE`, `production_activation_allowed=False`, and
  `qualification_only=True`.  Its constructor rejects an attempted activation.
- The inertness test proves that both default and attached Fabric perform an
  ordinary ingest against `MemoryGraph` without touching a native database
  (`tests/test_substrate_runtime_binding.py`).

Therefore an already-qualified component is not a production replacement
until its live caller, data, read/recovery behavior, and retained external
owners are qualified together.

## Production applicability matrix

The terms below are intentionally about the initial storage-substitution
profile, not full TORMENT parity.  `MAY_REMAIN_EXTERNAL_TO_NATIVE_DATABASE`
does not waive an interface: an external owner must retain its current inputs
and outputs when the selector is eventually introduced.

| Capability | Classification | Current evidence and cutover meaning |
| --- | --- | --- |
| Bounded ordinary CREATE, REINFORCE, DISTINCT, CONTRADICTION, and NO_WRITE storage outcomes | `QUALIFIED_AND_CORE_CLOSED` | D1/V2 closes the identified storage comparison for its Character-free private core profile.  This is not a proof that the live Fabric gate, query, or all configured production paths are native-routed. |
| Storage retrieval | `REQUIRED_BLOCKER` | Current `query` calls `MemoryGraph.search` for private and shared lanes.  Qualified native readers/search primitives are not selected from the application path. |
| Restart and recovery of core memories | `REQUIRED_BLOCKER` | `MemoryGraph._load()` rebuilds current state from append-only `nodes.jsonl`; no production native-core recovery/hydration route replaces that behavior. |
| Qualified post-write core | `QUALIFIED_BUT_NOT_PRODUCTION_WIRED` | The staging adapter qualifies its bounded core profile, but current ingest calls `LegacyFabricPostWriteAdapter`.  The native pre-effect gate explicitly refuses unavailable effects rather than silently falling back. |
| Character seed planting and seed provenance | `REQUIRED_BLOCKER` | Character is enabled by default.  `create_agent` plants seed memories into the private graph, attaches them through the legacy motif registry, and persists `seed_eids` plus `seed_motif_id`.  The frozen source fact is `SEED_PROVENANCE_TRANSLATION=NOT_REPRESENTABLE_IN_CURRENT_VOCABULARY`; a vocabulary change is not authorized. |
| Character drift measurement | `QUALIFIED_BUT_NOT_PRODUCTION_WIRED` | C1A qualified measurement under an explicit staging profile and retains `CharacterStore` externally.  It does not make Fabric select a native route. |
| Character gravity correction | `QUALIFIED_BUT_NOT_PRODUCTION_WIRED` | C1B qualified the narrow correction sequence in staging only.  The production selector and Character seed/context compatibility remain absent. |
| Checkpoint snapshots | `MAY_REMAIN_EXTERNAL_TO_NATIVE_DATABASE` | Checkpoints are documented as convenience, non-authoritative JSON snapshots; missing/corrupt checkpoints replay durable memory.  Native database ownership is not required.  A later production route must preserve the external checkpoint call boundary when it is due. |
| Persistent trajectory evidence | `MAY_REMAIN_EXTERNAL_TO_NATIVE_DATABASE` | Trajectory artifacts are external diagnostic/persistence evidence, not current core-memory authority.  EID observations still require explicit scoped compatibility where consumed. |
| Motif attach/create below split conditions | `QUALIFIED_BUT_NOT_PRODUCTION_WIRED` | Native motif read/decision/composition work is qualified in staging, while ordinary ingest still invokes `LegacyMotifRuntimeAdapter.attach_or_create`. |
| Motif auto-split and membership retirement | `REQUIRED_BLOCKER` | Legacy `MotifRegistry.AUTO_SPLIT_ENABLE` is true.  At 96 members and the radius/improvement gates, it rewrites the parent membership and creates a child.  Native C1B explicitly returns `CHARACTER_MOTIF_SPLIT_PARITY_REQUIRED` before a prospective 96th member.  No native membership retirement/removal parity is qualified. |
| Bridges | `MAY_REMAIN_EXTERNAL_TO_NATIVE_DATABASE` | `BridgeRegistry` is an external JSON owner over domain and motif aliases.  It may remain external, but a native shared-lane reader must prove alias-compatible bridge peeks; no bare motif-ID substitution is safe. |
| Compression and deep-memory lane | `DEFERRED_NOT_REQUIRED_FOR_INITIAL_CUTOVER` | Compression is disabled by default and the deep lane is entered only when enabled.  This does not authorize disabling an already-enabled deployment: it must either retain its external owner unchanged or receive a separately qualified profile before that deployment cuts over. |
| Shared-domain/shared-lane storage | `REQUIRED_BLOCKER` | `/agent/ingest` accepts `scope` with `shared` as a documented option and `ingest` directly writes `ws.shared_graphs[chosen_domain]`; query always reads ranked shared lanes.  It is production-reachable, so a private-only route cannot replace production storage. |
| Query integration | `REQUIRED_BLOCKER` | The public query/retrieve paths have no native selector and directly assemble results from legacy graphs, motifs, and optional bridges/deep results. |
| Existing-workspace migration | `REQUIRED_BLOCKER` | Existing services admit and rehearse frozen snapshot evidence under explicit scope plans.  There is no qualified live existing-workspace cutover/migration plus recovery path for the production graph roots. |
| Production selector/activation boundary | `QUALIFIED_BUT_NOT_PRODUCTION_WIRED` | There is no selector, Fabric native write selection, dual write, dual read, deployment transition, or cutover.  The current staging capability intentionally rejects activation; implementation is blocked by the preceding semantic closures. |

## Character conclusion

`CharacterStore` itself can remain an external JSON owner, but Character as a
whole cannot truthfully remain untouched outside a native core replacement.
Its persisted `seed_eids` and `seed_motif_id` are not passive annotations:
`measure_drift()` resolves them through the graph cache and motif registry,
and `gravity_correction()` creates a graph memory and attaches it to the seed
motif.  Seed planting does the same at agent creation.

There is no current architecture showing those references can continue to
operate unchanged against a native core without a provenance translation and
typed graph/motif compatibility boundary.  The frozen provenance fact forbids
inventing that translation in this phase.  Consequently:

```text
CHARACTER_REQUIRED_FOR_CUTOVER = YES
CHARACTER_STORE_REQUIRED_FOR_NATIVE_OWNERSHIP = NO
CHARACTER_PROVENANCE_VOCABULARY_CHANGE = NOT_AUTHORIZED
CHARACTER_D1_SUBARM = DEFERRED
```

## External-store conclusion

Checkpoint and trajectory files are not required to become SQLite tables.
They are legitimate retained side stores, provided the production route
continues to invoke their existing external contract with qualified,
namespace-scoped identifiers wherever an EID crosses the boundary.

```text
CHECKPOINT_REQUIRED_FOR_NATIVE_OWNERSHIP = NO
TRAJECTORY_REQUIRED_FOR_NATIVE_OWNERSHIP = NO
```

The native staging post-write adapter presently refuses checkpoint, trajectory,
bridge, and deep-memory effects when its explicit profile marks them required.
That is correct fail-closed staging behavior, not evidence that those owners
must migrate to SQLite.  The eventual selector must instead either compose
their retained contracts or refuse a deployment profile that has not been
qualified.

## Minimum production route

`PRODUCTION_NATIVE_ROUTE_READY` means all of the following are true for the
specific deployment profile being selected:

1. Existing private and production-reachable shared graph state has a
   qualified scoped migration/admission and native restart/recovery path.
2. Every displaced write and read behavior—selection, CREATE/REINFORCE/
   DISTINCT/CONTRADICTION/NO_WRITE result, motif state, retrieval, and
   post-write orchestration—has an integrated parity witness, not merely a
   component test.
3. Character seed/provenance, drift, gravity, and context references either
   have their qualified native-compatible boundary or that deployment has no
   reachable Character behavior.  The ordinary default profile does reach it.
4. The reachable motif auto-split branch has qualified membership retirement,
   or the unchanged external owner remains in place with an explicit,
   semantics-preserving boundary.
5. Retained checkpoint, trajectory, bridge, and optional deep-memory owners
   are explicitly composed and their scoped inputs/outputs remain compatible.
6. Only then can a production selector be separately qualified for activation,
   rollback, and deployment-state transition.

This is intentionally less than `FULL_TORMENT_BEHAVIOR_PARITY`: unrelated
external side stores need not move into SQLite.  It is nonetheless stricter
than component readiness because every behavior actually displaced by native
storage must be qualified.

## Dependency-ordered blockers

The smallest current blocker list is five items.  Each item identifies a
capability rather than proposing an unauthorized implementation.

| ID | Description | Why required | Current owner | Native status | Smallest safe closure |
| --- | --- | --- | --- | --- | --- |
| BLOCKER-1 | Existing-workspace scoped migration, native read, and restart/recovery | Current durable memory rebuild and public retrieval are legacy graph operations.  A replacement cannot strand existing graph roots or read only new writes. | `MemoryGraph` JSONL/shards and frozen-snapshot admission tools | Component/snapshot qualification exists; no live production migration or recovery route | Prove a scoped, idempotent existing-workspace admission plus native recovery/read against real persisted production-shaped roots. |
| BLOCKER-2 | Character provenance and graph/motif compatibility | Character is enabled by default and stores functional seed EID/motif references.  Current vocabulary cannot represent the seed provenance. | `CharacterStore`, `MemoryGraph`, `MotifRegistry` | C1A/C1B staging pieces qualified; seed/context/provenance and Fabric composition unresolved | Authorize and qualify a truthful provenance vocabulary or prove a lossless external compatibility adapter; do neither by invention. |
| BLOCKER-3 | Reachable motif auto-split membership retirement | Legacy production automatically rewrites membership at the configured split conditions.  Native intentionally refuses that state transition. | `MotifRegistry` | Attach/create/read geometry qualified below the branch; retirement not qualified | Qualify parent-member retirement and child publication atomically, including retry/recovery and reader parity. |
| BLOCKER-4 | Shared-domain lane and bridge-compatible query path | Shared ingest is externally selectable and query reads shared lanes on every normal request.  Bridges carry external motif aliases across those domains. | Workspace shared `MemoryGraph`s, `MotifRegistry`, `BridgeRegistry` | No production shared route or native query integration | Qualify shared state migration/read/write and alias-safe external bridge composition. |
| BLOCKER-5 | Production Fabric selection and integrated deployment qualification | The sole live path is legacy; the native capability refuses activation.  A selector before blockers 1–4 would turn a staging experiment into unqualified production behavior. | `app.py` / `TormentFabric` | Deliberately inert, STAGING-only | After blockers 1–4, qualify a single production selection, retained-side-store orchestration, rollback, and deployment transition without dual authority. |

```text
AUTO_SPLIT_REQUIRED_FOR_CUTOVER = YES
SHARED_STORAGE_REQUIRED_FOR_CUTOVER = YES
PRODUCTION_SELECTOR_IMPLEMENTATION_BLOCKED_BY_SEMANTICS = YES
PRODUCTION_SELECTOR_IMPLEMENTATION_READY_ONCE_REMAINING_BLOCKERS_CLOSE = YES
PRODUCTION_SELECTOR_IMPLEMENTATION_READY = NO
```

Recommended next work is `BLOCKER-1`: the bounded existing-workspace native
read/recovery and scoped admission boundary.  It is first because both
Character compatibility and shared-lane selection need stable, qualified
native identities and restart behavior to bind against.  It must remain
separate from a production selector.

## Inertness declaration

```text
CORE_STORAGE_SUBSTRATE_QUALIFIED = YES (bounded D1/V2 core profile)
FULL_PRODUCTION_BEHAVIOR_PARITY_READY = NO

PRODUCTION_FILES_CHANGED = 0
SUBSTRATE_FILES_CHANGED = 0
MIGRATION_FILES_CHANGED = 0

NATIVE_ACTIVE = NO
DUAL_WRITE = NO
DUAL_READ = NO
CUTOVER_OPENED = NO

7G5E0_PRODUCTION_APPLICABILITY_AUDIT_COMPLETE = YES
```
