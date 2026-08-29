# TORMENT Memory Substrate — Phase 7G4 inert runtime binding (v0.1)

Phase 7G4 adds an explicit, programmatic STAGING binding seam between
`TormentFabric` and an already-qualified native core. It is configuration
only: attached does not mean active, bound does not mean authoritative, and
STAGING does not mean cutover.

## Current runtime remains unchanged

`TormentFabric` continues to own the configured embedder, its
`TriOctaMemoryKernel`, and private `MemoryGraph` instances. `Workspace`
continues to construct shared-domain `MemoryGraph` instances directly.
`torment_service.app` continues to construct its global Fabric as
`TormentFabric(data_dir=DATA_DIR)`, with no native binding. There is no app
configuration, endpoint, environment selector, or restart behavior that can
select native storage.

The optional keyword-only Fabric argument is:

```python
TormentFabric(data_dir, native_memory_binding=prepared_binding)
```

Without it, `native_memory_binding` and its readiness result are `None`.
With it, the immutable binding is retained privately and is never consumed by
ingest, retrieval, workspace/graph construction, proposal or motif handling,
Character, compression, or deep-memory workflows. No `MemoryGraph` is
replaced, and no dual read, dual write, shadow read, fallback, or routing is
introduced.

## Binding preparation

`prepare_native_memory_runtime_binding(...)` accepts a caller-opened qualified
SQLite connection only while it validates facts. The returned
`NativeMemoryRuntimeBinding` stores no connection or cursor—only its resolved
existing database path, core UUID, STAGING role, typed scope bindings, and an
explicit `NativeRepresentationLane`. Preparation does not bootstrap a core,
create schema, migrate, or persist semantic state.

The factory fails closed unless all of the following hold:

* The existing file-backed core path exactly matches the prepared connection.
* The loaded runtime and schema pass existing qualification.
* The caller-supplied UUID is the core metadata UUID.
* The core role is `STAGING` and deployment state is `LEGACY_ACTIVE`.
* The lane is the qualified 7G3B/7G3C `COMPAT_EMBEDDING`/generation-1/
  `compat-embedding-v1`/`RAW_VECTOR`/`float32` lane.
* Every typed scope references durable identity, semantic, and legacy-source
  namespace rows.

`ACTIVE_CORE`, `NATIVE_ACTIVE`, and `EVIDENCE_ONLY` are refused. The binding
has no activation method and readiness always states `activation_allowed=False`.

## Explicit scopes and lane

`NativeMemoryRuntimeScope` is structurally either `PRIVATE_AGENT` with an
`agent_id`, or `SHARED_DOMAIN` with a `domain_id`; the other qualifier is
forbidden. Each scope includes a workspace ID plus explicit identity,
semantic, and legacy compatibility-source UUIDs. Duplicate scope keys and
shared compatibility namespaces fail preparation. Human-readable identifiers
in different workspaces remain distinct; neither paths nor EIDs derive UUID
identity.

`NativeRepresentationLane` includes provider, model, dimension,
representation class, generation, derivation contract, encoding, and dtype.
`validate_fabric_embedder(...)` compares the Fabric-owned embedder to that
lane before attachment. Provider, model, and dimension must all match;
equal-dimensional, different-model embedders are refused. The binding module
does not call `build_embedder_from_env`, instantiate Hash/SentenceTransformer/
Ollama providers, or make network calls. Fabric’s normal constructor still
performs its existing single embedder construction; binding validation neither
rebuilds nor replaces that embedder.

## Inertness and authority

Attachment creates zero native objects, revisions, relationships,
representations, operations, transitions, integrity records, reconciliation
records, or `ACTIVE_AUTHORIZATION` records. Fabric does not retain a global
SQLite connection. The qualified test core’s semantic row counts remain
unchanged while ordinary legacy Fabric ingest and `MemoryGraph` search run.

The current authority remains legacy runtime storage. A binding is not an
authorization, capability, semantic transition, cutover witness, or production
database. H1–H8 remain implemented for their applicable native semantic paths;
7G4 adds no semantic carrier or transition path and does not widen H1–H8.

## Deferred caller adaptation

The bounded 7G2B findings remain deferred to 7G5: Fabric workflows use legacy
EIDs before canonical flush, Character workflows use legacy EIDs during
pre-flush enrichment, and promotion performs immediate flush rather than the
same pre-finalization identity flow. 7G4 does not reserve native EIDs or add a
Fabric-specific draft workaround. Native drafts retain their no-precommit-EID
invariant. Caller adaptation is required before any 7H cutover machinery can
consider making native storage authoritative.

## Deliberate exclusions

There is no provider factory in substrate code, activation switch, active-core
attachment, app change, startup core creation, production core, migration,
live persistence wiring, current-authority change, search acceleration, or
cutover in this phase.
