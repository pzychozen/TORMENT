# TORMENT Native Memory Convergence and Decommission Plan

## Status, objective, and non-goals

```text
CONVERGENCE_PLAN_STATUS = READY_FOR_REVIEW
DOCUMENT_KIND = PROPOSED_ARCHITECTURE_AND_RETIREMENT_PLAN
DELETION_AUTHORIZATION = NO
REAL_CUTOVER_AUTHORIZATION = NO
REAL_MEMORY_REEMBED_AUTHORIZED = NO
BLOCKER_5_REOPEN_REQUIRED = NO
```

The desired end state is semantic convergence, not an arbitrary reduction in
line count:

```text
ONE_ACTIVE_PUBLIC_MEMORY_RUNTIME = YES
ONE_QUERY_COGNITION_IMPLEMENTATION = YES
ONE_POST_WRITE_SEMANTIC_IMPLEMENTATION = YES
ONE_VECTOR_RUNTIME_GEOMETRY = YES
ONE_DEPLOYMENT_AUTHORITY = YES
ACTIVE_LEGACY_MEMORY_WRITE_PATH = NO
ACTIVE_LEGACY_MEMORY_QUERY_AUTHORITY = NO
NATIVE_RUNTIME_LEGACY_FALLBACK = NONE
```

“One implementation” means one active implementation of each memory
semantic.  It does not move CharacterStore, roles, bridges, checkpoints,
trajectory evidence, deep memory, conflict/hivemind state, or other external
owners into SQLite.  Their ownership boundaries remain explicit.

```text
NATIVE_*_RUNTIME_MAY_OWN_SEMANTIC_ADAPTER = YES
SEMANTIC_ADAPTER_OWNERSHIP != DURABLE_STORE_OWNERSHIP
```

A native adapter may own the correct native-memory interaction semantics for
Character, trajectory/checkpoint, world/SRG, or another retained-owner
boundary.  The external subsystem still owns its durable or process-local
state.  Native integration therefore does not imply SQLite absorption.

This plan does not delete code, rewrite historical experiments, invalidate
Blocker-5 evidence, or create a second production runtime.  During
qualification, coexistence means fenced evidence and import support, never
dual public read/write authority.

## Post-I4 ratification supersession

The detailed post-I4 root-wide activation contract is frozen in
`TORMENT_MEMORY_SUBSTRATE_POST_I4_ROOT_WIDE_CONVERGENCE_RATIFICATION_v0.1.md`.
It supersedes this plan's pre-Phase-9D future-tense assumptions about
root-scope membership, bounded native public fallthrough, and root-wide
administration integration. This plan remains the lifecycle/retirement roadmap;
the ratification is authoritative for owner-specific geometry disposition,
P2/P6/P7 sequencing, completion-witness v2, writer-freeze and discovered-census
requirements, and the continued prohibition on real activation or retirement.

## Lifecycle classes

Every semantic component in the ledger below receives exactly one class:

| Lifecycle class | Meaning |
|---|---|
| `PERMANENT_NATIVE_RUNTIME` | Survives as active production memory semantics after full qualification. |
| `PERMANENT_MIGRATION_IMPORT_SUPPORT` | Retained for bounded future imports/forensics, never a public memory authority. |
| `TRANSITIONAL_DUAL_RUNTIME` | Temporary adapter during qualification; fenced so it cannot create dual public authority. |
| `LEGACY_ACTIVE_RUNTIME_TO_RETIRE` | Current legacy production semantic path to isolate/delete only after retirement gates. |
| `QUALIFICATION_ONLY` | Read-only preflight, rehearsal, or diagnostic machinery not needed for ordinary runtime/import. |
| `EXPERIMENT_EVIDENCE` | Isolated experimental fixture/harness evidence; not production substrate authority. |
| `TEST_CONTRACT` | Tests pinning a distinct invariant or recovery contract. |
| `DOCUMENTATION_EVIDENCE` | Historical or architectural documents/receipts. |
| `EXTERNAL_OWNER_NOT_PART_OF_SUBSTRATE` | A retained owner reached through a bounded port, not reimplemented by the substrate. |

The unit of classification is a semantic component, not necessarily a whole
Python module.  A public facade and its legacy storage branch, for example,
have different lifecycles and must not be retired as an inseparable file.

Brainvision is intentionally outside this plan: it is not a substrate source,
runtime, import input, compatibility source, or convergence target.

Every `TRANSITIONAL_DUAL_RUNTIME` component must be explicitly
`REAFFIRMED` or `RETIRED` at each implementation-phase boundary.  Transitional
classification may not survive indefinitely by inertia.

## Component lifecycle ledger

| Semantic component / present surface | Lifecycle class | Planned disposition |
|---|---|---|
| SQLite schema, connection/transaction layer, objects, revisions, provenance, relationships, payload policy, IDs, and representation records in `torment_service/substrate/` | `PERMANENT_NATIVE_RUNTIME` | Retain as the durable native memory model, subject to normal schema governance. |
| Native compatibility facade and typed native memory access | `PERMANENT_NATIVE_RUNTIME` | Retain as the compatibility surface over native truth, not as a legacy graph adapter. |
| `NativeCompatEmbeddingReader`, `NativeMemoryVectorRuntime`, and production vector runtime | `PERMANENT_NATIVE_RUNTIME` | Retain as the single active target-lane vector geometry. |
| `NativeQualifiedQueryReadModel` and native query cognition integration | `PERMANENT_NATIVE_RUNTIME` | Become the only active query cognition/read-model implementation. |
| `NativeMemoryRuntimeScope`, `NativeFabricRoutingScope`, native routing capability/router, and native world/SRG runtime | `PERMANENT_NATIVE_RUNTIME` | Retain and generalize to root-qualified scope registry keys. |
| Native public ingest executor, receipt store, prepared-ingest storage adapter, and native route recovery | `PERMANENT_NATIVE_RUNTIME` | Retain as the single public mutation/recovery path after activation. |
| `NativeFabricPostWriteAdapter`, native post-write memory access, native derived-memory and native shared post-write consumers | `PERMANENT_NATIVE_RUNTIME` | Retain as the single post-write semantic implementation, retaining explicit external-owner ports. |
| Native motif reader, composition, decision adapter, split/merge, and motif geometry ports | `PERMANENT_NATIVE_RUNTIME` | Retain as the active motif runtime, generalized for empty typed shared lanes. |
| Deployment selector, deployment-core maintenance, agreement resolver, and `NativeProductionResourceOwner` | `PERMANENT_NATIVE_RUNTIME` | Retain as one root-wide deployment authority and request-scoped resource owner. |
| Root-scope-membership relation and generalized root runtime index | `PERMANENT_NATIVE_RUNTIME` | Add only after qualification; it binds lawful root scope membership without duplicating namespace, object, representation, external-owner, or selector state. |
| Snapshot/inventory primitives and explicit source-evidence manifest support | `PERMANENT_MIGRATION_IMPORT_SUPPORT` | Retain for bounded import and recovery evidence, never for public queries/writes. |
| Identity/object/relationship/representation/motif/deep-memory/proposal admission services | `PERMANENT_MIGRATION_IMPORT_SUPPORT` | Retain as import machinery; generalize only where root profile qualification requires it. |
| Existing-workspace admission, generalized successor, B3A/B3B representation bootstrap, motif projection/re-geometry, and admission recovery descriptors | `PERMANENT_MIGRATION_IMPORT_SUPPORT` | Retain for future controlled imports; ensure they never select public authority. |
| Offline cutover controller and writer-drain/activation evidence | `PERMANENT_MIGRATION_IMPORT_SUPPORT` | Retain as administrative migration support, with root-wide profile input after qualification. |
| Existing B1/B5 read-only readiness reports and runtime qualification reports | `QUALIFICATION_ONLY` | Retain while they independently establish readiness; later consolidate only if an equivalent invariant remains. |
| Deployment diagnostics and static preflight tools | `QUALIFICATION_ONLY` | Retain as diagnostics, not as runtime selection mechanisms. |
| Legacy `MemoryGraph` graph/shard search, write, flush, and graph initialization semantics | `LEGACY_ACTIVE_RUNTIME_TO_RETIRE` | Retire from active public authority after gates; retain only explicit raw source readers needed for import. |
| Legacy `Workspace` graph construction and `TormentFabric` legacy workspace/agent graph ownership branch | `LEGACY_ACTIVE_RUNTIME_TO_RETIRE` | Replace with root-native resolution after activation; split out any still-needed shared cognition preparation rather than retaining graph authority. |
| `LegacyQualifiedQueryReadModel` and legacy query lanes | `LEGACY_ACTIVE_RUNTIME_TO_RETIRE` | Retire when native read-model/cognition evidence passes the generalized production profile. |
| Legacy post-write adapter and legacy `memory_runtime_access` graph-backed access | `LEGACY_ACTIVE_RUNTIME_TO_RETIRE` | Retire as active semantics when all qualified native post-write behavior is live. |
| Legacy motif registry/file-backed active motif access | `LEGACY_ACTIVE_RUNTIME_TO_RETIRE` | Retire from active runtime only after native motif geometry and empty-shared semantics are qualified. |
| Legacy public REST/MCP/backend branch that delegates memory behavior to `MemoryGraph` | `LEGACY_ACTIVE_RUNTIME_TO_RETIRE` | Remove after native public transport is the only enabled backend under selector agreement. |
| Backend-selection/public delegation shim used while converting callers | `TRANSITIONAL_DUAL_RUNTIME` | Must select exactly one backend per root and refuse ambiguity; remove after all public callers use the native owner. |
| `PublicTormentRuntime.__getattr__` and legacy `TormentFabric` delegation fallthrough | `TRANSITIONAL_DUAL_RUNTIME` | It currently lets still-unconverted public, metadata, or external-owner surfaces reach legacy `TormentFabric` while native runtime is active.  Retire only after every native-allowlisted route has an explicit surviving owner; final state is `PUBLIC_FACADE_LEGACY_FALLTHROUGH = REMOVED`. |
| Legacy-to-native compatibility facades that invoke both representations for comparison | `TRANSITIONAL_DUAL_RUNTIME` | Keep only until their parity/recovery evidence is frozen; never use them as a dual read/write authority. |
| Historical dry/wet-run migration wrappers in `torment_service/migration/` that do not form the qualified substrate import path | `QUALIFICATION_ONLY` | Preserve until mapped to an equivalent import invariant or archived as historical evidence. |
| Isolated rehearsals, manual operator harnesses, and non-production fixture runners | `EXPERIMENT_EVIDENCE` | Preserve or archive by evidence value; do not make them public runtime dependencies. |
| Invariant tests for identity, isolation, recovery, idempotency, query/post-write semantics, authority, representations, and migration | `TEST_CONTRACT` | Retain; consolidate only duplicate assertions that add no distinct invariant. |
| Phase records, qualification documents, cutover receipts, architecture specifications, and this plan | `DOCUMENTATION_EVIDENCE` | Retain as immutable historical/design evidence, versioned by supersession rather than rewritten. |
| CharacterStore, role state, BridgeRegistry, checkpoints, trajectory evidence, deep memory, conflict/hivemind services, and other retained side stores | `EXTERNAL_OWNER_NOT_PART_OF_SUBSTRATE` | Retain under their own owner contracts and access them only through qualified ports. |

### Permanent `COMPAT` identifier decision

```text
COMPAT_EMBEDDING_IS_PERMANENT_NATIVE_REPRESENTATION_CLASS_IDENTIFIER = YES
IDENTIFIER_STABILITY = INTENTIONAL_COMPATIBILITY_CONTRACT
```

`COMPAT_EMBEDDING`, `NativeCompatEmbeddingReader`, and the compatibility
facade name a stable representation/interface contract, not a temporary
permission for legacy geometry or dual authority.  The permanent target lane
is still `st / BAAI/bge-small-en-v1.5 / 384`.  After convergence, a separate
human-facing/module-name cleanup may be considered only when it preserves the
identifier contract or supplies an explicitly qualified rename/migration gate.
R6B does not rename code.

### Source-family coverage map

The preceding ledger is semantic rather than file-by-file.  To prevent an
unclassified module being treated as an accidental exception, the currently
relevant source families have the following single classification.  A future
component may not be added to the programme without one row and one class.

```text
SOURCE_FAMILY_MAP_RECONCILED_AGAINST_ACTUAL_RELEVANT_DIRECTORY_AT_EACH_FREEZE = YES
```

| Source family | Lifecycle class | Boundary |
|---|---|---|
| `substrate/{schema,connection,objects,object_revision_governance,provenance,relationships,payload_policy,representations,reconciliation,ids,deployment_types,errors}` | `PERMANENT_NATIVE_RUNTIME` | Core durable model and governance. |
| `substrate/{canonical_intent,memory_runtime_order,derived_memory}` | `PERMANENT_NATIVE_RUNTIME` | Inspected shared canonical-intent, runtime-order, and closed derived-memory primitives used by active native semantics. |
| `substrate/{compat,compat_query,compat_embedding_reader,native_memory_runtime_access,native_memory_vector_runtime}` | `PERMANENT_NATIVE_RUNTIME` | Native compatibility/read/vector surface after legacy graph retirement. |
| `substrate/{fabric_translation,fabric_native_routing,native_world_runtime,native_srg_runtime,native_public_ingest_executor,native_public_mutation_receipts,production_native_owner}` | `PERMANENT_NATIVE_RUNTIME` | Native public routing, mutation, and process-local runtime semantics. |
| `substrate/{native_post_write_runtime,native_derived_memory_runtime,native_character_seed_plant,native_character_drift_runtime,native_character_gravity_runtime,native_direct_shared_ingest,native_trajectory_evidence_runtime}` | `PERMANENT_NATIVE_RUNTIME` | Active post-write and retained-owner integration implementations. |
| `substrate/{motifs,motif_runtime_reader,motif_decision_adapter,native_motif_split,native_motif_merge_runtime,memory_motif_composition,memory_reinforcement,shared_proposal_materialization,authorized_proposal_receipts}` | `PERMANENT_NATIVE_RUNTIME` | Native motif/proposal/reinforcement semantics. |
| `substrate/{deployment_selector,deployment_core_maintenance}` | `PERMANENT_NATIVE_RUNTIME` | The root authority resolver and controlled-core lifecycle required by the active native runtime. |
| `substrate/offline_cutover_controller` | `PERMANENT_MIGRATION_IMPORT_SUPPORT` | Root activation administration, never an ordinary public runtime dependency. |
| `substrate/migration/{snapshot,inventory,admission,identity_admission,existing_workspace_admission,existing_workspace_multi_scope_admission,representation_admission,motif_admission,proposal_admission,deep_memory_admission}` | `PERMANENT_MIGRATION_IMPORT_SUPPORT` | Bounded legacy import/admission evidence. |
| `substrate/migration/{runtime_embedding_input,runtime_normalization,runtime_reembedding_bootstrap,runtime_representation_bootstrap,runtime_motif_projection,runtime_motif_regeometry_projection,legacy_governance}` | `PERMANENT_MIGRATION_IMPORT_SUPPORT` | Representation/motif import and normalization support. |
| `substrate/migration/character_seed_normalization` and `substrate/character_seed_witness` | `PERMANENT_MIGRATION_IMPORT_SUPPORT` | Inspected bounded Character seed source/witness normalization; it retains external Character ownership and cannot activate routing. |
| `substrate/migration/{runtime_readiness,workspace_runtime_readiness,rehearsal}` plus `substrate/{runtime_qualification,runtime_binding,closed_child_qualification,deployment_diagnostic}` | `QUALIFICATION_ONLY` | Readiness, closure, and diagnostic evidence; no public authority. |
| Legacy `memory_graph`, legacy graph portions of `fabric`, legacy `memory_runtime_access`, legacy `post_write_runtime`, legacy `motifs`, and legacy query lanes | `LEGACY_ACTIVE_RUNTIME_TO_RETIRE` | Current graph-based public authority to be retired only after the stated gates. |
| Legacy generic migration package under `torment_service/migration/` | `QUALIFICATION_ONLY` | `OLD_GENERIC_MIGRATION_PACKAGE_DISPOSITION = QUALIFICATION_ONLY`; retire after an equivalent native import invariant is qualified.  Its survivor is the bounded `substrate/migration/` import family, or the package is removed once no unique invariant remains. |
| `public_runtime` backend-selection wiring and `PublicTormentRuntime.__getattr__` during caller conversion | `TRANSITIONAL_DUAL_RUNTIME` | A temporary boundary with one selected authority per root; it may never activate dual reads/writes or retain implicit legacy fallthrough after every allowlisted route has an explicit owner. |
| Focused substrate/authority/recovery regression suites | `TEST_CONTRACT` | The executable invariant record. |
| Phase specifications, qualification receipts, and architecture plans in `docs/` | `DOCUMENTATION_EVIDENCE` | Historical and design evidence. |
| Character, roles, bridges, checkpoints, trajectories, deep memory, conflict/hivemind, and other side stores | `EXTERNAL_OWNER_NOT_PART_OF_SUBSTRATE` | Independent owners reached through explicit ports. |

## Duplication debt ledger

Duplication is tracked by semantic function, not by lines of code.  A
duplicate remains only while it has a stated proof obligation and an exit
gate.

| Semantic function | Legacy owner | Native owner / eventual survivor | Why both exist now | Retirement prerequisite |
|---|---|---|---|---|
| Memory object reads | `MemoryGraph`, legacy `Workspace` graph views | Native compatibility facade plus native memory runtime access | Native representation was introduced without changing public authority. | Generalized root admission, active reader recovery, and native read verification for all admitted scope classes. |
| Memory writes | `TormentFabric.ingest` legacy graph mutation and `MemoryGraph` write/flush | Native public ingest executor, router, facade, and receipt recovery | Native storage/recovery was qualified before public backend selection. | Controlled native public write/replay/restart verification on the real admitted root. |
| Query read model and cognition | `LegacyQualifiedQueryReadModel` / legacy lanes | `NativeQualifiedQueryReadModel` | Native query implementation was qualified under fenced owners while legacy remained public. | Root-wide qualified query cognition, representation normalization, namespace isolation, and production read verification. |
| Vector access and search | Legacy shard/load/search logic in `MemoryGraph` | `NativeCompatEmbeddingReader` and native vector runtime | Needed to prove native raw-vector behavior before authority change. | One target ST/BGE lane across all materialized scopes; no hash/unknown scope pending. |
| Post-write semantic effects | Legacy post-write adapter and graph-backed runtime access | Native post-write adapter and typed native memory access | Native consumers were ported incrementally while legacy public writes stayed live. | Every enabled production post-write consumer passes native write/recovery/restart evidence. |
| Motif access and geometry | File-backed `MotifRegistry` / legacy motif readers | Native motif reader, composition, split/merge, geometry port | Admission and projection required historical motif source while native motif runtime matured. | Target-lane motif re-geometry plus empty-shared/motif-only and cross-workspace isolation qualification. |
| Memory routing | Legacy workspace/domain dispatch in `TormentFabric` | Native routing capability and `NativeFabricMemoryRouter` | Storage routing had to be proven independently of public transport. | Root-qualified scope registry and native route verification for multi-workspace/multi-private topology. |
| Public-runtime delegation | Legacy REST/MCP/Fabric path | Selector-agreement-gated native production owner/executor | B5 intentionally qualified owner/executor before changing transport. | Native backend is selected for the full root, all public callers use it, and no legacy fallback remains. |
| Public facade fallthrough | `PublicTormentRuntime.__getattr__` → legacy `TormentFabric` | Explicit route owner or external-owner port for every allowlisted public surface | The native public runtime still needs a temporary delegation surface for unconverted callers. | Every native-allowlisted route has an explicit surviving owner; then remove fallthrough rather than narrowing it indefinitely. |
| Admission and recovery | Historical generic migration wrappers | Substrate snapshot/admission/B3/B4/B5 and generalized root successor | Multiple phases accumulated evidence-specific runners. | Generalized explicit-source admission qualification; then isolate old wrappers as evidence or remove where redundant. |
| Workspace and agent scope handling | Legacy path-derived `Workspace` and agent initialization | Immutable root descriptor plus root-scope-membership relation | Legacy persistence topology is the import source; durable active membership is not yet implemented. | Root profile and post-activation creation qualification, including external identity gates. |
| Compatibility façade | Legacy public shapes plus direct graph calls | Native compatibility façade over native truth | Callers need stable shapes while ownership moves. | Public callers consume the native façade/typed outputs; no direct graph shape remains. |

No row permits a permanent duplicate active production semantic.  In
particular, a compatibility façade may remain, but it must delegate only to
native truth after convergence.

## Required implementation phases

The smallest safe implementation sequence implied by the root profile and
this plan is:

1. **Root descriptor and explicit evidence qualification.** Implement and
   qualify the immutable multi-workspace/multi-private admission description,
   owner-bounded manifest, expected-absence witnesses, and root-atomic
   recovery.  Do not use recursive root fingerprinting.
2. **Legacy representation source extension.** Qualify the metadata-less
   per-EID source adapter for `ws3`, `ws4`, and `ws5`, including canonical text
   continuity, retained evidence, B3B derivation, and recovery.
3. **Root-wide target representation and motif qualification.** Generalize
   B3/B4/B5 over all materialized scopes, establish one ST/BGE geometry, and
   prove empty shared/motif-only behavior.  This is normalization, not ranking
   parity preservation.
4. **Root runtime and native scope creation.** Generalize recovery caches,
   query/routing/post-write lookups, and operation identities to complete root
   scope keys.  Add the narrowly defined root-scope-membership relation and
   gated native creation of workspace/private/shared scopes without legacy
   graph fallback.
5. **Production-shaped generalized rehearsal.** Exercise restart/recovery,
   root-atomic activation, public reads/writes, idempotency, external-owner
   boundaries, and no legacy-memory use in isolated roots.
6. **Separately authorized real admission and activation.** Only after an
   operator authorizes it, admit the real root, activate once, and collect
   controlled native read/write/restart evidence.
7. **Stabilization and semantic retirement.** After defined stability
   evidence, remove active legacy branches in dependency order and retain only
   bounded import readers and historical evidence.

No phase authorizes a legacy/native dual-write or dual-read production window.
If a proposed implementation needs one, it is outside this plan and requires a
new explicit architecture decision.

## Retirement gates and post-gate actions

Legacy code is eligible for deletion or isolation only after all of these
gates have passed:

```text
GENERALIZED_NATIVE_PROFILE_QUALIFIED = YES
REAL_PRODUCTION_ADMISSION_COMPLETE = YES
ROOT_WIDE_NATIVE_ACTIVATION_COMPLETE = YES
CONTROLLED_NATIVE_READ_WRITE_VERIFIED = YES
RESTART_AND_RECOVERY_VERIFIED = YES
POST_ACTIVATION_SCOPE_CREATION_QUALIFIED = YES
DEFINED_STABILIZATION_EVIDENCE_COMPLETE = YES
NATIVE_RUNTIME_LEGACY_FALLBACK = NONE
PUBLIC_FACADE_LEGACY_FALLTHROUGH = REMOVED
```

Until then, legacy is the production source/oracle for the selected root and
must not be deleted merely because a native counterpart exists.

After the gates, each legacy surface receives one concrete action:

| Post-gate action | Applies to |
|---|---|
| `DELETE` | Active legacy graph/query/write/post-write/motif runtime branches and obsolete backend selection paths once no active caller can reach them. |
| `RETAIN_READ_ONLY_FOR_IMPORT` | Explicit legacy source parsers, manifest readers, and representation-evidence adapters required to import a later legacy root.  They may not construct active public graph authority. |
| `RETAIN_AS_HISTORICAL_EVIDENCE` | Frozen qualification fixtures, old receipts, failure forensics, experiments, and documents whose scientific or operational history remains useful. |
| `RETAIN_BECAUSE_EXTERNAL_OWNER` | Character, role, bridge, checkpoint, trajectory, deep-memory, and other non-substrate owner systems. |

Deletion is a separate reviewed change for each semantic row.  It must cite
the gates and demonstrate that an equivalent native or retained-import owner
exists.  There is no blanket deletion command and no LOC target.

## Test and evidence policy

Tests remain first-class contracts where they pin a distinct invariant:

```text
identity and namespace isolation
source immutability and recovery
idempotency and lost-response handling
query semantics and result provenance
post-write semantic effects
deployment authority fences
representation identity and lane isolation
migration/admission/recovery evidence
external-owner boundaries
```

Tests may be consolidated only when the replacement asserts the same invariant
with no lost failure mode.  Historical scientific evidence is not a candidate
for deletion merely because it is not production code.  Experiment fixtures
may later be archived or isolated, but their results are not rewritten.

## Completion criteria

The convergence programme is complete only when the following are true in the
qualified and activated target profile:

```text
SEMANTIC_DUPLICATION_RETIRED = YES
TRANSITIONAL_RUNTIME_REMOVED = YES
ACTIVE_AUTHORITY_SINGLE = YES
EXTERNAL_OWNER_BOUNDARIES_PRESERVED = YES
ACTIVE_LEGACY_MEMORY_QUERY_AUTHORITY = NO
ACTIVE_LEGACY_MEMORY_WRITE_PATH = NO
```

A smaller repository may follow from these conditions.  It is not itself the
measure of success.
