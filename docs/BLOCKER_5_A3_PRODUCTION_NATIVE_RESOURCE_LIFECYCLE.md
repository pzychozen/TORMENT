# Blocker-5 B5-A3 — Production Native Resource Lifecycle

## Status

`B5-A3` qualifies a private, direct-use resource boundary for one already
selected `ACTIVE_CORE/NATIVE_ACTIVE` core.  It does not make REST, MCP,
`TormentFabric`, ingest, or query choose native storage.

```text
B5_A3_PRODUCTION_NATIVE_RESOURCE_OWNER = QUALIFIED
PRODUCTION_NATIVE_OWNER_REQUIRES_NATIVE_AGREEMENT = YES
ACTIVE_CORE_RECOVERY = QUALIFIED
PRODUCTION_QUERY_CONTEXT = QUALIFIED
PRODUCTION_WRITE_CONTEXT = QUALIFIED
SERVICE_GLOBAL_RAW_SQLITE_CONNECTION = NONE
REQUEST_SCOPED_SQLITE_OWNERSHIP = QUALIFIED
PRODUCTION_SRG_STATE_OWNER = SERVICE_PROCESS
PRODUCTION_WORLD_STATE_OWNER = SERVICE_PROCESS
REQUEST_SCOPED_VECTOR_CURRENTNESS = PASS
PRODUCTION_WRITE_THEN_QUERY = PASS
PRODUCTION_RESTART_RECOVERY = PASS
STAGING_CAPABILITY_GUARD_PRESERVED = YES
PRODUCTION_NATIVE_CONTEXT_LEGACY_FALLBACK = NONE
PRODUCTION_NATIVE_DEEP_PROFILE = REFUSED
DEPLOYMENT_RESOLVER_SIDE_EFFECTS = NONE
PUBLIC_NATIVE_OWNER_CONSTRUCTION = NONE
PUBLIC_INGEST_BACKEND = LEGACY
PUBLIC_QUERY_BACKEND = LEGACY
DUAL_WRITE = NO
DUAL_READ = NO
CUTOVER_OPENED = NO
KERNEL_FILES_CHANGED = 0
```

## Owner and authority boundary

`NativeProductionResourceOwner` is intentionally separate from the frozen
`NativeFabricRoutingCapability`; the latter remains `STAGING`,
`LEGACY_ACTIVE`, qualification-only, and incapable of production activation.

The owner can be constructed only by presenting an exact, current B5-A2
`NATIVE_AGREEMENT` plus an admission descriptor. It re-resolves at
construction and freezes the data root, selector generation, selected core
UUID and contained path, descriptor/profile digests, core witness, and the
exact qualified SQLite runtime witness. The descriptor must match the selected
digest/core and its lane/scope plan must match the effective deployment profile.
A bare path, UUID, environment flag, or boolean is not authority.

Before every context is opened, the owner resolves the agreement again. A
selector/core/profile/runtime change, missing core, descriptor drift, or
malformed authority record refuses before native effect; it never falls back
to legacy. Write routing repeats active recovery immediately before its native
route, and the production route capability independently checks
`ACTIVE_CORE/NATIVE_ACTIVE(core_id)` on its bounded connection.

The resolver itself remains facts-only. It still opens no resource owner,
vector runtime, public backend, or semantic writer.

## Active recovery and resources

`recover_active_existing_workspace_native_multi_scope_runtime` is a narrow,
separate recovery path. It derives the core path from the agreement's
contained selector field rather than accepting one from a caller. It validates
the active core/deployment row, descriptor digest and UUID, representation lane,
and the complete existing admitted scope/domain order. It returns the same
recovered-runtime shape consumed by `NativeQualifiedQueryReadModel`.

The original staging recovery still calls the staging-only runtime binding
unchanged. The active recovered scope uses an active-only vector resource that
shares the established vector-search/rebuild implementation; no SQL-ranking or
query-cognition algorithm was added.

The service owner stores no SQLite connection. It owns only immutable authority
facts and process-local SRG state, world state, and motif process order. Every
query/write context is created for one thread and one synchronous operation;
the native vector reader now explicitly rejects cross-thread use in addition to
SQLite's same-thread connection discipline. A context opens/uses/closes its
own reader resources. Write routing opens and closes its qualified connection
inside the operation. The owner closes registered contexts, prevents new ones,
and discards only process-local state; repeated close is safe.

## Query, write, freshness, and restart

Production query contexts construct the existing `NativeQualifiedQueryReadModel`
with the owner's `NativeSRGProcessState`. Existing callers that omit that
optional argument retain a self-owned state. SRG math is unchanged and remains
process-local: read-side SRG evolution publishes no SQLite successor.

Production write contexts use the existing native memory router, compatibility
facade, representation publication, motif composition, native SRG/world
runtime, and idempotent route machinery beneath a distinct active capability.
They require a claimed scope, exact active agreement, matching lane, and stable
operation key. `STAGING`, pending, and legacy states cannot qualify that path.
External owners such as CharacterStore, BridgeRegistry, conflict/hivemind
services, trajectory/checkpoint artifacts, and deep-memory stores are not
absorbed by this owner.

Request-scoped vectors rebuild from current READY truth. A native write followed
by a new query context observes the newly published memory, while independent
contexts have distinct SQLite readers. Closing and recreating an owner against
the same agreement recovers durable memory/query truth and fresh vector
matrices; intentional process-local SRG overlays are discarded on restart.

## Qualification evidence

`tests/test_b5_a3_production_native_resource_owner.py` covers non-native
agreement refusal (`LEGACY_PUBLIC`, `MAINTENANCE_ONLY`, and `REFUSED`), deep and
profile/runtime drift, exact construction, active-core loss, close behavior,
same-owner independent readers, cross-thread rejection, active write-to-fresh
query visibility, a shared source plus private mood-derived READY lane with an
unrelated lane unchanged, SRG process continuity/restart reset, read-only query
non-mutation, and the retained staging guard. Focused B5-A2, binding/routing,
vector, post-write, D1 trace, A2 native-query, A3 cognition, public REST, and
MCP regressions are recorded with this change.

`torment_service.app` and `torment_service.mcp_server` neither import nor
construct the owner. Public startup remains legacy even when a temporary test
root reaches an exact agreement.

## Remaining boundary

`B5-A4` is next only with separate authorization: explicit public Fabric
backend selection/startup mode, `LEGACY` or `NATIVE`, never dual authority.
This slice opens neither that selector nor a real cutover.
