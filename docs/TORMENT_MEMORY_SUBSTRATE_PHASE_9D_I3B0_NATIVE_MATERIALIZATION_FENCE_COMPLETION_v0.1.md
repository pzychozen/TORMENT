# P9D-I3B0 — Native Materialization Fence Completion

## 0. Boundary incident and corrected evidence scope

During I3B0 implementation, one broad documentation search accidentally
surfaced search-result snippets from historical files whose names and content
mentioned Brainvision.  A later attempt to locate the requested orientation
record also opened one general historical recovery roadmap that contained a
single Brainvision mention.  No Brainvision source or code file was opened,
inspected, modified, compared, or used in this phase.  No finding, design
choice, test, or implementation decision below derives from either exposure.
Neither source will be revisited.

```
P9D_I3B0_BRAINVISION_BOUNDARY_INCIDENT =
    INCIDENTAL_DOCUMENTATION_MENTION_EXPOSURE_ONLY

BRAINVISION_SEARCH_SNIPPETS_EXPOSED = YES
BRAINVISION_DOCUMENTATION_MENTION_OPENED = YES
BRAINVISION_CODE_OPENED = NO
BRAINVISION_CODE_INSPECTED = NO
BRAINVISION_FILES_TOUCHED = 0
BRAINVISION_INFORMATION_USED_FOR_I3B0 = NO
SECOND_REPOSITORY_COGNITIVE_FUNCTION_INSPECTED = NO
I3B0_FINDINGS_DERIVED_FROM_BRAINVISION = NO

BRAINVISION_FILES_READ = NOT_CERTIFIABLE_AS_ZERO
```

All subsequent source inspection is restricted to the explicit I3B0
allowlist: `torment_service/app.py`, `torment_service/fabric.py`,
`torment_service/public_runtime.py`,
`torment_service/query_read_model.py`,
`torment_service/substrate/production_native_owner.py`, their directly
identified state-owner modules, and focused I3B0/B5/A3 test fixtures.

## 1. Status

This receipt is being completed under the corrected boundary.  It will record
the materializer census, fences, focused offline tests, and deferred I3B/I3C
gates before any commit decision.

## 2. I2 correction, preserved foundation

I2 correctly established these primary-entry protections:

```
GET_WORKSPACE_NATIVE_FALLBACK = BLOCKED
CREATE_AGENT_NATIVE_FALLBACK = BLOCKED
NATIVE_ACTIVE_ENTRY_MATERIALIZATION = STRUCTURALLY_BLOCKED
```

I3A adversarial review found that this did not by itself prove every
downstream helper reached after an admitted native query was
non-materializing.  I2 is neither retracted nor characterized as an
architectural error.  Its claim is narrowed as follows:

```
FULL_NATIVE_ROUTE_LEGACY_MATERIALIZATION = NOT_YET_PROVEN (pre-I3B0)
FULL_NATIVE_ROUTE_MATERIALIZER_CENSUS = REQUIRED
FULL_NATIVE_ROUTE_LEGACY_MATERIALIZATION = CORRECTED_IN_I3B0
```

## 3. Bounded materializer census

The denominator is every state-materializing operation transitively reachable
from a native-admitted public route, explicit native public runtime surface,
`TormentFabric.query`, native qualification helper, or native side-store
adapter.  It is not a count of raw `os.makedirs` call sites.

| Materializer | Caller / route | Native reachable | State created or mutated | Owner | I3B0 disposition |
|---|---|---:|---|---|---|
| `get_workspace` → `Workspace` construction | legacy branch of `TormentFabric.query`; public/direct fallthrough | Conditional legacy only | workspace metadata, domains, graphs, registries, policies | Legacy | I2 callee fence; native disposition requires pre-existing view/state |
| `create_agent` | legacy branch of `TormentFabric.query`; public/direct fallthrough | Conditional legacy only | identity, agent directory, graph/context | Legacy | I2 callee fence; native disposition uses pre-existing identity/context |
| `CollectiveField.__init__` | query → `_collective_query_context` → `_get_collective_field` | Conditional: Hivemind enabled | `workspaces/<ws>/collective` | Legacy external collective owner | Native query refuses before construction |
| `ArchiveStore.__init__`, including its SQLite-index acquisition route | `POST /retrieve` → `_get_archive_store` | Conditional: archive recall enabled | `memory_archive` and possible index/cache state | Legacy archive owner | Native `/retrieve` refuses before core/archive composition |
| `increment_retrieval_counts` | `POST /retrieve` archive-hit promotion | Conditional: archive recall yields hits | durable retrieval-counter JSON | Legacy archive owner | Unreachable after the same native archive refusal |
| `_affect_state_path` | query mood-spiral read; `_FabricDerivedMemorySideStore.load_affect_state` | Conditional | agent directory before `affect_state.json` read | External affect owner | Native reads pass `materialize_parent=False`; explicit saves retain legacy/write behavior |
| `RoleStore.load(create_if_missing=True)` | query → `_role_context` | Conditional | default `roles.json` | External role owner | Native disposition passes `read_only=True`; absent evidence returns in-memory default |
| `_save_anchor_state` / `_save_affect_state` | explicit qualified native post-write side-store configuration | Conditional explicit write only | external anchor/affect durable state | External post-write owner | Not a query/read path; retained as a named post-write composition boundary |
| `_save_symbol_state`, deep-store attachment, warmup creation | legacy deep retrieval helper | Native branch blocked | symbol/deep/warmup state | Legacy deep-memory owner | Native deep profile refuses before helper; no native deep fallback |
| `CharacterStore` load methods | query Character assembly | Yes, read only | none on load | External Character owner | Preserved read adapter; no migration or post-write conclusion |
| `_ReadOnlyBridges` / `_ReadOnlyConflictRegistry` | native workspace view/query conflict and bridge reads | Yes, read only | none | External bridge/conflict owners | Non-materializing reader; malformed/unreadable conflict evidence refuses |
| `IdentityStore` / `RoleStore` / `CharacterStore` constructor base-root `mkdir` | initial Fabric composition before an admitted request | Factory composition only | existing selected root only | Legacy external-store constructors | Not a request-scoped workspace/agent materializer; selected root must pre-exist and I2 guards all lazy scope entry |

No unclassified state materializer remains reachable from an admitted native
read route in this bounded census.  The maintained I3B0 test holds the named
route-to-materializer references and fails when an entry is removed or a
current root reference is not represented.

## 4. Fences completed

### Collective

The review finding was confirmed:

```
TormentFabric.query
  -> _collective_query_context
  -> _get_collective_field
  -> CollectiveField.__init__
  -> legacy collective directory creation
```

When collective/Hivemind query context is applicable, a qualified native query
now raises `NativeQueryReadRefused` before that constructor.  The public
facade translates the lower-layer refusal into its structured native-public
refusal.

```
COLLECTIVE_QUERY_NATIVE_DISPOSITION = REFUSE_WHEN_APPLICABLE
COLLECTIVE_QUERY_NATIVE_PARITY = NOT_YET_QUALIFIED
COLLECTIVE_QUERY_ACTIVATION_GATE = OPEN
```

No third scope kind was added and no collective migration occurred.

### Archive composite retrieval

`POST /retrieve` previously could create an `ArchiveStore` and persist
retrieval counts after core retrieval.  In native mode with archive recall
applicable, it now returns HTTP 409 before core query, archive construction,
and counter update.  When archive recall is explicitly disabled by profile,
the non-archive selected core retrieval remains available.

```
ARCHIVE_RECALL_NATIVE_PARITY = NOT_YET_QUALIFIED
ARCHIVE_RETRIEVAL_COUNT_WRITE = COMPOSITION_GATE
ARCHIVE_RECALL_NATIVE_DISPOSITION =
    REFUSE_UNTIL_PARITY_OR_EXPLICIT_INAPPLICABILITY
```

The REST classifier no longer grants native authority to every `/archive/`
path.  The maintained explicit archive inventory is intentionally empty until
a route has a qualified native disposition.

```
NEW_FUTURE_ARCHIVE_ROUTE = REFUSED_UNTIL_EXPLICITLY_CLASSIFIED
NATIVE_ARCHIVE_ROUTE_CLASSIFICATION = EXPLICIT_FAIL_CLOSED
```

### Affect and role reads

`_affect_state_path` now separates read path selection from parent-directory
creation.  Legacy reads and explicit writes preserve historical behavior;
qualified native reads request a path without `mkdir`.  The native-derived
side-store uses that same disposition.

`NativeQualifiedQueryReadModel` and `NativeProductionQueryContext` explicitly
carry `native_read_disposition=True`.  `TormentFabric.query` derives the
non-materializing behavior from that disposition rather than relying solely on
the private `_native_public` transport flag.  A native qualification call must
use pre-existing workspace, identity, agent state, and kernel context; it may
not call `get_workspace` or `create_agent`.  Native role reads consequently
use `read_only=True` and cannot persist a default profile.

```
NATIVE_AFFECT_READ_MATERIALIZATION = BLOCKED
NATIVE_ROLE_DEFAULT_CREATION = BLOCKED
NATIVE_QUERY_QUALIFICATION_DISPOSITION =
    MATCHES_NATIVE_PUBLIC_READ_DISPOSITION
```

### Conflict evidence

`_ReadOnlyConflictRegistry` now uses the lower-level
`NativeQueryReadRefused` contract for malformed or unreadable evidence.
`_build_conflict_map` propagates that deliberate refusal while retaining the
historical fail-soft behavior for unrelated legacy registry failures.  Missing
native conflict files remain an empty result.

```
CONFLICT_NATIVE_REFUSAL_SWALLOWED = NO
```

## 5. Frozen semantics and deferred gates

No query mathematics or ordering policy changed.  Existing observable order
remains the target: legacy lane row order, legacy domain declaration/insertion
order, legacy motif registry order, and stable merge/final-sort order.  No new
EID, motif-ID, or runtime-ID tie policy was introduced.

Native motif float reduction is parity-load-bearing because low-order centroid
differences can alter domain routing.  Native motif iteration must therefore
match legacy semantic iteration; parity is blocked if retained evidence is
insufficient.

```
PRESERVE_EXISTING_OBSERVABLE_ORDERING = YES
NEW_QUERY_TIE_BREAK_POLICY = NO
FLOAT_REDUCTION_ORDER_IS_SEMANTICALLY_LOAD_BEARING = YES
I3_QUERY_PARITY_INPUT_REQUIREMENT = SAME_QUALIFIED_REPRESENTATION_STATE
NEW_B3A_B3B_QUERY_DEPENDENCY = NO
```

The native vector stale-snapshot behavior remains a named I3B blocker:

```
STALE_NATIVE_QUERY_SNAPSHOT_DISPOSITION =
    DEFERRED_TO_I3B_DETECTABLE_ADAPTER_REFUSAL
```

I3C retains the named composition gates:

```
SRG_QUERY_READ_PARITY = REQUIRES_NAMED_SOURCE_EQUIVALENCE_TEST
SRG_QUERY_MUTATION_PARITY = UNRESOLVED
SRG_QUERY_POSTWRITE_COMPOSITION_GATE = OPEN
CHARACTER_QUERY_PARITY = ADAPTER_FEASIBLE
CHARACTER_QUERY_EXTERNAL_OWNER = PRESERVED
```

## 6. Focused offline qualification

The focused I3B0 inventory contains ten tests covering collective refusal,
archive refusal, archive route fail-closed behavior, affect no-creation,
qualified role no-creation, malformed and absent conflict semantics, optional
side-path non-materialization, legacy defaults, and the maintained census.
It ran only against synthetic pytest roots using the deterministic test
embedder and the writable isolated pytest base directory.

Regression coverage also reran the qualified I2 public-native fence and the
I3A full Fabric cognition parity suite.  No service, real root, external
provider, or real re-embedding was used.

## 7. Final I3B0 status

Subject to the final diff review and immediate port preflight:

```
P9D_I3B0_NATIVE_MATERIALIZATION_FENCING = PASS
FULL_NATIVE_ROUTE_MATERIALIZER_CENSUS = COMPLETE
FULL_NATIVE_ROUTE_LEGACY_MATERIALIZATION = FENCED
QUERY_COGNITION_CHANGED = NO
POST_WRITE_COGNITION_CHANGED = NO
TORMENT_MATHEMATICS_PRESERVED = YES
BLOCKER_5_REOPEN_REQUIRED = NO
REAL_PRODUCTION_ACTIVATION = NOT_AUTHORIZED
```
