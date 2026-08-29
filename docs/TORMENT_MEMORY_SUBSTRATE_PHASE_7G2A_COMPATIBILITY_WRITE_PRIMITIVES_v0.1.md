# TORMENT Memory Substrate — Phase 7G2A Compatibility Write Primitives v0.1

Phase 7G2A adds a deliberately narrow native-only write boundary for ordinary
core-memory source state.  It translates the useful semantic portion of the
current `MemoryGraph` flow without recreating its JSONL physical behavior:

`create_memory_state` publishes a native UUID object, immutable native R1, a
native object-revision transition/effect/output, and a scoped `EID` alias in
one semantic `BEGIN IMMEDIATE` transaction.  `EID` is only
`legacy_source_namespace + EID + integer text -> object`; it is never an
object, revision, transition, or operation identity.  Allocation is
`max(committed EID aliases) + 1` within that transaction, so migrated `1,2,8`
leads to `9`, namespaces may each contain `9`, and rollback publishes neither
object nor alias.

The public façade is `NativeMemoryCompatibilityFacade` in
`torment_service.substrate.compat`.  Both create and patch require the caller
to supply a durable idempotency namespace and key.  An identical retry,
including a retry after a lost response, resolves the same native operation,
object, revision, transition, and EID.  A changed intent with that identity is
rejected.  The source namespace, identity namespace, semantic scope, and
idempotency namespace must already be registered native rows.

Creation builds structural native state directly: scope, lifecycle,
governance, authority category, provenance reference, and object kind are
columns on the immutable revision.  A supplied valid lifecycle envelope is
translated to structural lifecycle state/authoritativeness; otherwise the
qualified protected-marker/default-UNSET behavior is used.  Ordinary memory
always receives `NOT_APPLICABLE`, never active authorization.  Authority-like
domain payload fields cannot change that structural category.  Scope-shaped
payload shadows are refused.

`patch_memory_state` resolves namespace plus EID to the current native object
inside the same semantic transaction, deterministically merges permitted
flexible fields, and publishes exactly one `NATIVE_ORDINARY` successor.  R1 is
unchanged, the current pointer advances atomically, and an optional expected
revision fails stale.  Retrying the same patch returns R2 rather than making
R3.  Generic patches reject structural keys: scope, lifecycle, governance,
authority category/authorization, provenance, native and revision identity,
representation/readiness, integrity, reconciliation, and operation/transition
identity.  Compression-shaped fields and `pos`/`vel`/`vel0` remain flexible
payload.

The existing bounded candidate gate is preserved before semantic side effects:
`CandidateShapedValue` is refused as summary, as the extra-payload object, or
as an immediate payload value.  The check is type-only and non-recursive.

There is no representation, embedding, READY state, search, relationship
write, staged `spawn_memory`, `flush_node`, `add_memory` drop-in claim,
`MEMORY_CREATE` event emulation, JSONL/file access, dual write, migration,
cutover, or live `MemoryGraph`/Fabric/compression/embedding-store wiring in
this phase.  The test suite uses qualified temporary STAGING cores only.
