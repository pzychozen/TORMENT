# TORMENT Memory Substrate — Phase 7G5B5

## Whole-workspace native runtime readiness and cutover preconditions

`NativeWorkspaceRuntimeReadiness` is a read-only qualification boundary for
one explicit legacy snapshot, STAGING native core, immutable runtime scope
plans, qualified `NativeRepresentationLane`, and explicit feature postures.
It creates no migration, representation, operation, transition, authority,
maintenance event, deployment marker, or file change.

```text
B1 admission/runtime classification
  -> A3D current COMPAT_EMBEDDING reader proof
  -> A3B NativeMotifRuntimeReader proof
  -> inert A3D binding/capability/post-write construction
  -> explicit feature and retained-side-store posture
```

B5 never runs B2, B3A, B3B, B4A, or B4B. An incomplete row remains an exact
migration blocker, not an instruction to repair it.

## Read-only guard

Before and after a report, B5 fingerprints every native user table and each
caller-supplied observation root. It reuses the rehearsal whole-core H1–H8
verifier and `PRAGMA foreign_key_check`. A changed table, file, or SQLite
change counter raises an invariant violation.

```text
durable_effect_count = 0
file_mutation_count = 0
embedder_call_count = 0
authority_expansion_count = 0
```

The qualification embedder is an identity-only DTO with `provider`, `model`,
and `dim`; it has no embed method. The A3D10 post-write configuration is
prepared but never run, so no world, SRG, side-store, or derived-memory work
executes.

## Closure and provenance inventory

Every B1 runtime memory is re-read through `NativeCompatEmbeddingReader`.
The report records B2+B3A, B2+B3B, or native-ready-without-migration lineage
from immutable representation output evidence. A reader contradiction blocks
closure.

Provider/model are intentionally not fields on the raw representation reader.
For B3-derived compatibility vectors, B5 also validates the immutable B3
PENDING-operation administrative lane witness. This proves the full
caller-owned target lane without changing raw vector retrieval.

Every admitted legacy motif maps to zero or one B4 target in the requested
namespace/lane. B4A and B4B are distinguished by typed transition kind; more
than one target is `WHOLE_WORKSPACE_MOTIF_PROJECTION_AMBIGUOUS`. Ready targets
are revalidated through the existing `NativeMotifRuntimeReader`, including
catalog state, ordered members, member vectors, radius, domain centroid, and
coherence projection. Every member must be a runtime-ready memory in scope.

## A3D constructibility, not routing

B5 builds the existing inert binding, routing capability, and A3D10
post-write adapter. It does not invoke Fabric, `TormentFabric.ingest`, a
DomainRouter, startup wiring, an environment selector, or a backend toggle.

`CORE_STAGING_RUNTIME_READY` requires closure, side-store EID compatibility,
H1–H8, zero migration-created active authorizations, and all three A3D
constructors under the reduced staging posture.

`FULL_PRODUCTION_BEHAVIOR_PARITY_READY` separately evaluates the caller's
explicit production posture. Current conditional blockers include Character,
Character gravity, compression, deep-memory runtime behavior, and motif
auto-merge. Operational blockers include motif suggestions, checkpoints,
persistent trajectory evidence, and bridge suggestions.

Production native routing and cutover are always `NO` in B5: production
selection, deployment-state transition, and cutover/rollback qualification
remain later work.

## Retained side stores

B5 reuses B1's inventory for conflicts, anchors, affect history, Hivemind,
identity/proposals, CharacterStore, deep-memory evidence, bridges,
checkpoints, trajectory evidence, and role state. Caller-observed side-store
EIDs must supply `legacy_source_namespace_id + EID`; a bare, ambiguous, or
missing observation becomes a compatibility blocker. B5 does not rewrite a
side store or move it to SQLite.

## Qualification declarations

```text
B5_WHOLE_WORKSPACE_RUNTIME_READINESS = COMPLETE
B5_IS_READ_ONLY = YES
B5_DURABLE_EFFECT_COUNT = 0
B5_FILE_MUTATION_COUNT = 0
B5_EMBEDDER_CALLS = 0

NATIVE_ACTIVE = NO
DUAL_WRITE = NO
DUAL_READ = NO
CUTOVER_OPENED = NO
A3D_NATIVE_ROUTE_WIRED_INTO_FABRIC = NO
```
