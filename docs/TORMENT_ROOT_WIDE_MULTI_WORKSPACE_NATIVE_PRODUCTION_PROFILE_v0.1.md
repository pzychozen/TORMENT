# TORMENT Root-Wide Multi-Workspace Native Production Profile

## Status and authority

```text
PROFILE_SPEC_STATUS = READY_FOR_REVIEW
DOCUMENT_KIND = PROPOSED_ARCHITECTURE_SPECIFICATION
IMPLEMENTATION_AUTHORIZATION = NO
REAL_MEMORY_REEMBED_AUTHORIZED = NO
REAL_PRODUCTION_CUTOVER_AUTHORIZED = NO
BLOCKER_5_REOPEN_REQUIRED = NO
```

This document defines the proposed production-shaped profile for one data
root.  It is a specification for later qualification and operator review; it
does not select a core, create an admission descriptor, contact a memory, or
authorize a cutover.

The profile continues the Blocker-5 authority model rather than replacing its
evidence:

```text
SEMANTIC_MEMORY_SCOPE = WORKSPACE
DEPLOYMENT_BACKEND_AUTHORITY = DATA_ROOT
ONE_DEPLOYMENT_AUTHORITY_PER_DATA_ROOT = YES
ONE_SELECTED_NATIVE_CORE_PER_DATA_ROOT = YES
PER_WORKSPACE_MIXED_LEGACY_NATIVE_AUTHORITY = NO
PHYSICAL_ROOT_SPLITTING = NO
```

The selected native core is root-wide.  It contains namespaces for many
workspaces; it is not one core per workspace and it is not a sidecar selected
independently by a workspace.

## Scope vocabulary

The following terms are deliberately distinct.

| Term | Meaning | Initial-admission treatment |
|---|---|---|
| Materialized memory scope | A private or shared graph lane with recognized memory source evidence. | Admit its memory objects, representations, and applicable motifs. |
| Identity-only agent scaffold | An agent identity exists, but it has no materialized private graph. | Record the external identity observation; do not create a native memory object or graph migration lane. |
| Declared-but-unmaterialized domain | A domain is declared, but has no materialized shared graph. | Record the declaration; do not invent a shared graph, memory row, or vector row. |
| Empty shared graph with motif state | A typed shared graph lane has zero memories and relevant motif state. | Admit a typed empty shared lane and motif state; admit no fake memory or representation rows. |
| No-memory-scope workspace | Workspace identity exists with no materialized private or shared graph lanes. | Record workspace identity only; it has no initial native memory runtime scope. |

`Empty shared graph with motif state` is not equivalent to an unmaterialized
domain.  The former has an existing typed graph/motif owner and must preserve
that empty state.  The latter has no graph owner to migrate.

## Frozen real-root admission census

The initial generalized profile must close against the R4-characterized
real-root census, not against a smaller convenient subset.  This is an
admission-time evidence target only; it does not inspect, mutate, or select
the real root.

```text
TOTAL_WORKSPACES = 50

MATERIALIZED_PRIVATE_LANES = 75
MATERIALIZED_SHARED_LANES = 44
TOTAL_MATERIALIZED_SCOPES = 119

QUALIFIED_ST_BGE_SCOPES = 66
HASH_SCOPES = 50
UNKNOWN_IDENTITY_SCOPES = 3

75 + 44 = 119
66 + 50 + 3 = 119
```

The frozen structural workspace shapes are:

```text
WORKSPACES_WITH_ZERO_PHYSICAL_PRIVATE_LANES = 3
WORKSPACES_WITH_ONE_PHYSICAL_PRIVATE_LANE = 40
WORKSPACES_WITH_FIVE_PHYSICAL_PRIVATE_LANES = 7

WORKSPACES_WITH_ZERO_PHYSICAL_SHARED_GRAPH_LANES = 6
WORKSPACES_WITH_ONE_PHYSICAL_SHARED_GRAPH_LANE = 44
```

The census includes the already characterized private-plus-shared,
multi-private, private-only, motif-only/empty-shared,
identity-only/declared-but-unmaterialized, and no-memory-scope shapes.  These
are structural categories, not a semantic relabelling of workspace names.

```text
ROOT_ACTIVATION_REQUIRES_COMPLETE_PROFILE_CLOSURE = YES
```

For this initial root admission, a descriptor that covers fewer than 119
declared materialized scopes cannot claim complete profile closure.  A
non-materialized scaffold is represented according to its own declared class;
it cannot hide a missing materialized scope.

### Census and manifest shelf life

```text
ADMISSION_CENSUS_VALID_ONLY_UNDER_WRITER_FREEZE = YES
ADMISSION_SOURCE_MANIFEST_VALID_ONLY_UNDER_WRITER_FREEZE = YES
```

If legacy writes resume after the census and source manifest are frozen, then:

```text
CENSUS_INVALIDATED = YES
MANIFEST_INVALIDATED = YES
RE_FREEZE_REQUIRED = YES
RE_CENSUS_REQUIRED = YES
```

A stale census or manifest is not activation evidence, even if its previously
recorded counts happen to look plausible.

## Canonical root and runtime scope identities

Every native scope, cache entry, recovery record, post-write lookup, motif
lookup, routing request, and operation key must resolve through a fully
qualified identity.  Numeric EIDs and bare agent/domain identifiers are never
root-wide keys.

```text
PrivateScopeKey = (workspace_id, PRIVATE, agent_id)
SharedScopeKey  = (workspace_id, SHARED, domain_id)
RootScopeKey    = (workspace_id, scope_kind, agent_id | domain_id)
```

Rules:

1. `workspace_id` is mandatory in every `RootScopeKey`.
2. Exactly one qualifier is present: `agent_id` for `PRIVATE`, `domain_id` for
   `SHARED`.
3. Native namespace IDs, operation/idempotency namespaces, cache keys,
   representation-reader keys, motif registry keys, and recovery-map keys are
   all derived from or bind the complete `RootScopeKey`.
4. A lookup with a missing, ambiguous, or cross-kind qualifier refuses.  It
   must not search another workspace, infer a domain from a path, or select the
   first matching EID.
5. A private and a shared scope may contain the same numeric legacy EID.  Their
   namespaces remain distinct because their `RootScopeKey` values differ.

This preserves the existing composite-identity requirement while making the
workspace component non-optional at the production root boundary.

## Production representation contract

The sole active production representation lane for this proposed profile is:

```text
provider = st
model    = BAAI/bge-small-en-v1.5
dimension = 384
encoding = RAW_VECTOR / float32
```

```text
HASH_VECTOR_BYTES_ARE_NOT_ST_BGE = YES
DIMENSION_EQUALITY_IS_NOT_REPRESENTATION_IDENTITY = YES
ACTIVE_ROOT_REPRESENTATION_LANES = 1
NATIVE_MIXED_REPRESENTATION_STORES = FORBIDDEN
NATIVE_ST_TO_HASH_CROSS_SPACE_COMPARISON = FORBIDDEN
```

```text
HASH_SCOPES_REQUIRING_TARGET_LANE_NORMALIZATION = 50 / 119
APPROXIMATE_MATERIALIZED_SCOPE_EXPOSURE = 42_PERCENT
```

The 42% figure is a proportion of initially materialized physical scopes, not
of memory objects, vector rows, bytes, or query traffic.  Possible changes to
vector geometry, relative ranking, and retrieval behavior therefore apply
across this substantial scope population; they are not a corner-case caveat.

For each materialized object, the active native representation must either be
an exact target-compatible captured representation or a qualified B3B-derived
target representation.  The source representation is retained as immutable
legacy evidence where it exists; it is not left active alongside the target
representation in the native production read geometry.

### Representation dispositions

| Source condition | Required disposition | Preconditions |
|---|---|---|
| Exact target-compatible captured vector | B3A byte derivation may be used. | Exact provider, model, dimension, encoding, dtype, integrity, and source evidence. |
| Hash representation | Qualified re-embedding to the target ST/BGE lane. | B1/B2 readiness, canonical source text, retained capture evidence, B3B identity/recovery contract, and target-lane validation. |
| Known incompatible/invalid representation | Qualified re-embedding to the target lane. | The applicable B3B strategy plus canonical source text and fail-closed recovery. |
| No vector present | Qualified target derivation only if canonical source text is valid. | B3B no-vector strategy; no invented legacy capture. |
| Unknown provider/model identity in the `ws3`, `ws4`, or `ws5` per-EID layout | Not initially admissible until a separate source-evidence extension qualifies it. | See “Metadata-less per-EID qualification.” |

Normalization preserves memory payload, memory/object identity, provenance,
and retained legacy representation evidence.  It may change active vector
bytes, retrieval geometry, and relative ranking.  Therefore:

```text
REEMBEDDING = REPRESENTATION_NORMALIZATION
REEMBEDDING != STORAGE_ONLY_BYTE_COPY
RANKING_PARITY_WITH_LEGACY_CROSS_SPACE_BEHAVIOR = NOT_CLAIMED
```

Normalization also does **not** automatically preserve the semantic freshness
of external-owner state that was previously derived from legacy vector
geometry.  Examples include character-drift measurements, motif-derived
character state, and SRG/geometry-derived retained markers where applicable.
Those stores remain external; R6B neither migrates them into SQLite nor
recomputes or invents a disposition for them.

```text
GEOMETRY_DERIVED_EXTERNAL_STATE_RECOMPUTED_BY_REEMBED = NO
GEOMETRY_DERIVED_EXTERNAL_STATE_DISPOSITION = UNRESOLVED_PRE_ACTIVATION_GATE
REAL_ROOT_NATIVE_ACTIVATION_REQUIRES_GEOMETRY_DERIVED_EXTERNAL_STATE_DISPOSITION = YES
```

Permitted future dispositions must be explicitly qualified as `RECOMPUTE`,
`INVALIDATE / REINITIALIZE`, `ACCEPT_AS_HISTORICALLY_STALE`, or another
explicitly qualified disposition.  This is a new real-root normalization
compatibility gate; it does not reopen Blocker-5.

The profile deliberately does not promote historical ST-query-to-hash-vector
comparison into a native contract.  Nor may ordinary post-activation writes
place ST/BGE bytes into a lane that remains active as hash geometry.

## Immutable generalized initial-admission description

The future generalized admission service must accept one immutable
`RootNativeProductionAdmissionDescription`.  It replaces first-profile
topology assumptions, without invalidating their historical qualification.

```text
RootNativeProductionAdmissionDescription
  schema_version
  data_root_identity
  admission_id and operator-bound idempotency identity
  immutable profile digest
  selected target representation lane
  ordered workspace plans
  explicit source-evidence manifest
  retained external-owner observations
  feature-posture and refusal declarations
```

Each `WorkspacePlan` contains:

```text
workspace_id
workspace identity metadata witness
ordered private scope plans (zero or more)
ordered shared scope plans (zero or more)
identity-only agent observations (zero or more)
declared-unmaterialized domain observations (zero or more)
no-memory-scope declaration when applicable
external-owner observations relevant to this workspace
```

Each materialized private or shared plan contains its full `RootScopeKey`,
source namespace identity, native memory/motif/idempotency namespace
identities, source-kind declaration, relevant node/edge/motif sources, source
representation evidence, target-lane binding, and per-stage recovery keys.
For an empty shared graph with motif state, the plan carries the shared scope
and motif evidence but has an explicit empty-memory set.

The plan order is canonical administrative order only:

```text
workspace_id lexical order
then PRIVATE agent_id lexical order
then SHARED domain_id lexical order
```

It is never a retrieval ranking, vector order, motif process order, or
semantic priority.

### Known first-profile generalization targets

The present qualified source deliberately contains narrow enforcement points;
they are implementation targets, not defects to patch in this documentation
phase:

```text
ExistingWorkspaceNativeMultiScopeAdmissionRequest.__post_init__
  -> exactly one PRIVATE_AGENT lane and at least one SHARED_DOMAIN lane

ExistingWorkspaceNativeMultiScopeDescriptor validation
  -> repeats the same first-profile topology law on recovery

NativePublicTormentRuntime._workspace_view
  -> exactly one recovered private scope for the workspace view
```

The generalized profile must replace these first-profile cardinality checks
with the root descriptor’s declared shape while retaining complete
workspace-qualified identity checks.  It must not relax them into an ambiguous
“choose any private scope” behavior.

### Topology invariants

```text
WORKSPACE_COUNT >= 1
PRIVATE_LANE_COUNT_PER_WORKSPACE >= 0
SHARED_LANE_COUNT_PER_WORKSPACE >= 0
PRIVATE_AGENTS_PER_WORKSPACE >= 0
ONE_SHARED_GRAPH_REQUIRED_PER_WORKSPACE = NO
ONE_PRIVATE_LANE_REQUIRED_PER_WORKSPACE = NO
ALL_MATERIALIZED_LANES_BIND_ONE_TARGET_LANE = YES
ROOT_ACTIVATION_REQUIRES_COMPLETE_PROFILE_CLOSURE = YES
```

An initially identity-only or unmaterialized scope is not an admission failure
merely because it has no graph.  A source declared materialized but lacking
required evidence is a failure; its absence must not be silently relabelled as
scaffolding.

## Explicit-source immutability evidence

The generalized profile replaces a whole-workspace recursive fingerprint with
an explicit owner-bounded evidence manifest.  The manifest is frozen before
admission and contains only canonical, owner-recognized locators:

```text
1. `workspace_meta.json` workspace identity metadata;
2. `domains.json`, `domain_policies.json`, and `bridges.json` where their
   owner contracts are relevant to the admitted result;
3. admitted `nodes.jsonl` and optional `edges.jsonl` sources;
4. explicit embedding manifests, shards, and maps;
5. recognized legacy embedding artifacts, including a qualified per-EID form;
6. relevant `motifs.json` state; and
7. explicit retained external-owner observations for identity, roles,
   character state, Character seed, checkpoint owner, trajectory owner,
   proposals, conflicts, and other explicitly qualified owner evidence.
```

Every entry binds its owner class, `RootScopeKey` where applicable, canonical
relative locator, expected presence or expected absence, byte length and
SHA-256 (for a present file), and a semantic role.  The manifest itself has a
canonical digest.  Expected absence is evidence for an empty graph, an
unmaterialized declaration, or a metadata-less layout only where the profile
explicitly says so.

Before every resume, recovery re-resolves each manifest locator within its
declared owner boundary and verifies the entry digest or expected absence.  It
also verifies the root profile digest, workspace/scope plan set, target lane,
and completed-stage witnesses.  A changed, missing, unexpectedly present, or
ambiguous owner artifact fails closed before reuse.

```text
EXPLICIT_SOURCE_MANIFEST_EQUIVALENCE = CONDITIONAL_ON_OWNER_CLASS_COMPLETENESS
OWNER_CLASS_COMPLETENESS = QUALIFICATION_OBLIGATION
```

The explicit set supplies equivalent admission/recovery assurance only when
the owner-class inventory is complete.  No source capable of changing the
admitted or native result may remain silently outside it.  An unrelated file
outside every declared owner set neither becomes a migration input nor changes
the frozen admission identity.  No recursive whole-workspace traversal is
permitted, and Brainvision remains excluded from the evidence boundary.

Manifest entry order is canonical evidence serialization only:

```text
MANIFEST_ORDER_IS_NOT = retrieval ranking
                        vector order
                        motif processing order
                        semantic priority
                        authority priority
```

## Generalized admission and recovery sequence

The future implementation must remain root-atomic even though work is
performed per scope.

```text
P0  Validate immutable root description and explicit evidence manifest.
P1  Create one inert STAGING core under the root’s legacy-active authority.
P2  Freeze and verify every declared source witness and expected absence.
P3  Admit B1/B2 for every materialized scope under fully qualified keys.
P4  Establish target representations: B3A only when exact; otherwise B3B
    only for qualified inputs and target identity.
P5  Project/re-geometry relevant motifs only in the target lane; preserve
    empty shared motif state without fabricated member vectors.
P6  Complete whole-profile reader, routing, post-write, external-owner, and
    recovery closure.  Every materialized scope must be ready.
P7  Persist one complete root admission witness.  Partial scope completion is
    recoverable staging evidence, never active production authority.
P8  A separately authorized controller may use the complete witness for one
    root-level activation.
```

The admission identity binds the root, canonical workspace and scope set,
source-evidence manifest digest, target lane, external-owner observation
digest, feature posture, and operator key.  Per-scope child keys include the
complete `RootScopeKey`; a retry cannot collide with the same agent/domain
name in another workspace.

Root activation is refused if any declared materialized scope is incomplete,
if an unknown-identity scope lacks its prerequisite qualification, if target
lanes differ, or if any evidence witness drifts.  There is no partial
workspace activation and no legacy/native per-workspace split.

## Metadata-less per-EID qualification requirement

The legacy layouts identified in `ws3`, `ws4`, and `ws5` are a separate,
bounded qualification prerequisite.  Provider/model identity must not be
inferred from their shared 384 dimension or from present `.npy` bytes.

Before they can enter a root admission description, a dedicated source adapter
must be qualified to establish all of the following:

```text
recognized per-EID source evidence and owner-bounded locators
canonical memory source availability for each candidate object
retained original representation evidence and integrity witness
mapping from source EID to admitted namespaced object identity
B3B-compatible target derivation and target-lane validation
interruption, retry, and idempotent recovery behavior
```

The adapter must not make a normal legacy workspace open create a new ST/BGE
metadata file and reinterpret that newly written metadata as historical
identity.  It must not discard the original per-EID bytes merely because the
target is derived from canonical text.

Until this qualification is complete, those three scopes remain
`UNADMITTED_UNKNOWN_REPRESENTATION_IDENTITY`, which blocks any root profile
that declares them materialized production memory scopes.

```text
METADATA_LESS_SCOPE_QUALIFICATION = REQUIRED_BEFORE_COMPLETE_ROOT_ACTIVATION
```

`ws3`, `ws4`, and `ws5` are materialized private scopes on the critical path;
they must never be recast as empty or unmaterialized merely to satisfy atomic
closure.

## Runtime ownership after activation

After a separately qualified activation, the root selector resolves one
`ACTIVE_CORE/NATIVE_ACTIVE` agreement.  The public runtime constructs one
native resource owner from that agreement and the complete root descriptor.
It does not construct a legacy `MemoryGraph` as a fallback.

The owner provides request-scoped native readers/writers, while process-local
state remains explicitly process-local.  Its root runtime registry maps only
complete `RootScopeKey` values to recovered native scope handles.  The same
key must be used by:

```text
query-read lane selection
vector matrix/rebuild cache
motif catalog and member lookup
post-write context lookup
native route selection
public ingest receipt namespace selection
recovery map and operation-key derivation
```

The runtime may cache a fully qualified handle, not a bare agent, domain,
workspace, source path, numeric EID, or mutable public request object.  A
request that does not name a lawful scope is refused before read or write.

### Query and write geometry

All query vectors and active memory vectors in a target scope use the one
qualified ST/BGE lane.  Cross-scope retrieval remains an explicit cognition
decision, not an accidental cache or directory scan; any such aggregation must
retain every contributing `RootScopeKey` in its result provenance.  A native
query does not compare target ST/BGE vectors with retained hash evidence.

Native writes select a qualified target scope before storage and publish only
the target representation lane.  They must not consult legacy graph search,
append to a legacy shard, or turn retained legacy vectors into active query
rows.  Post-write behavior uses the native semantic implementation with the
same scope key and continues to consult external owners only through their
defined ports.

## Scope-lifecycle durability decision

The initial admission description is immutable evidence, but it cannot be the
sole durable record for post-activation scope lifecycle.  Review of the
existing native primitives establishes that a distinct durable
root-scope-membership relation is required.

```text
NO_NEW_PARALLEL_SCOPE_REGISTRY = NO
ROOT_SCOPE_MEMBERSHIP_RELATION = REQUIRED
```

This is not a casual second database abstraction.  Existing
`semantic_scopes`, identity namespaces, legacy-source namespaces, and
idempotency namespaces own individual identifiers.  Object revisions bind an
effective semantic scope only after an object exists.  The present admission
descriptor is staging/import evidence, and the deployment selector owns core
authority, not per-scope membership.  None of these facts durably binds an
empty or newly created scope’s complete root identity to the namespace set,
target lane, external-owner witness, and active root profile after restart.

The future relation’s unique invariant is therefore:

```text
one complete RootScopeKey
  -> one lawful set of existing namespace/scope identities
  -> one target representation lane
  -> one external-owner identity witness
  -> one active-root-profile membership/lifecycle fact
```

It must be expressed through the existing native semantic operation and
namespace machinery where possible, and it must not duplicate object,
representation, external-owner durable state, or deployment-selector state.
R6B deliberately does not choose its schema or implementation.

## Post-activation native scope creation

The immutable initial admission description is not a permanent ban on creating
new native scopes.  A future implementation uses the root-scope-membership
relation under the active deployment agreement and target representation lane.

Permitted creation cases are:

| Request | Required prior authority and evidence | Native result |
|---|---|---|
| New workspace | Exact active root agreement; externally owned workspace identity; explicit operator/request idempotency identity; target lane match. | Register a new workspace namespace with zero memory objects. |
| New private agent in an existing workspace | Exact active agreement; externally owned agent/role/character identity observation; complete `(workspace_id, PRIVATE, agent_id)` key. | Register an empty native private scope ready for future native writes. |
| Permitted new shared domain | Exact active agreement; externally owned domain declaration; complete `(workspace_id, SHARED, domain_id)` key; configured policy permitting the domain. | Register an empty typed shared scope; motif state remains empty unless a lawful native operation creates it. |

The scope-membership operation must bind the deployment generation, root core UUID,
complete scope identity, scope kind, external identity witness, target lane,
and stable idempotency key.  It is refused if the selector agreement drifts,
the identity already maps differently, the namespace would collide, the domain
is not permitted, or an external-owner witness is absent.

Creation of an empty native scope is not fabrication of a memory object or a
legacy namespace.  It creates no legacy `MemoryGraph`, no legacy vector shard,
and no mixed authority.  Later native ingest is the only path that may create
the first native memory object and its target representation.

External identity, role, CharacterStore, bridge, checkpoint, trajectory, and
deep-memory owners retain their existing ownership.  Scope creation observes
or invokes their explicit contracts; it does not absorb them into SQLite or
manufacture identity from a filesystem path.

## Administrative boundaries

```text
NATIVE_WORKSPACE_CLONE = REFUSED_PENDING_SEPARATE_QUALIFICATION
REAL_ROOT_NODES_AND_EMB_1 = OUTSIDE_PUBLIC_WORKSPACE_AUTHORITY
ROOT_LEVEL_LEGACY_ANOMALY = PRESERVE_UNTOUCHED
ROOT_LEVEL_LEGACY_ANOMALY_INITIAL_ADMISSION_INPUT = NO
ROOT_LEVEL_LEGACY_ANOMALY_CLEANUP_TARGET = NO
```

The root-level `data/nodes.jsonl` and `data/emb_1.npy` anomaly is not a
workspace lane and is excluded from this profile.  This specification neither
inspects, migrates, deletes, nor reclassifies it.

## Required qualification gates before real use

This profile is ready for review, not ready for production execution.  Later
implementation and evidence must establish, at minimum:

1. generalized descriptor, explicit-evidence, and root-atomic recovery tests;
2. qualified metadata-less per-EID source extension where required;
3. target-lane B3B normalization and motif re-geometry evidence across the
   actual supported topology, with no ranking-parity claim;
4. multi-workspace/multi-private namespace-isolation, cache, query, routing,
   and post-write tests;
5. native post-activation scope-creation authority and recovery tests;
6. a production-shaped generalized admission rehearsal; and
7. separately authorized real-root admission, activation, controlled
   read/write verification, and restart/recovery verification.

No gate is satisfied by this document alone.
