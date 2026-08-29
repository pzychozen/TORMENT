# TORMENT Memory Substrate — Phase 7G3C text-search compatibility (v0.1)

Phase 7G3C adds a thin, native-only text query adapter at
`torment_service.substrate.compat_query`.  It is the query-derivation half of
the current `MemoryGraph.search(text, ...)` behavior only; it does not change
that legacy method or wire the native substrate into Fabric or Character.

## Boundary and injected dependency

`search_text(...)` requires a caller-injected `QueryEmbedder`-compatible
object with `provider`, `model`, `dim`, and `embed(text)`.  The caller supplies
a fully explicit `CompatibilityQueryLane`: expected provider/model/dimension,
representation class, generation, derivation contract, encoding, and dtype.
The adapter therefore neither imports nor calls `build_embedder_from_env`,
selects an embedding provider, reads embedding environment variables, creates
concrete providers, or requires network access.

The only currently qualified native lane is:

* `COMPAT_EMBEDDING`, generation `1`, `compat-embedding-v1`
* `RAW_VECTOR`, `float32`

The caller's expected provider and model must exactly match the injected
embedder before embedding.  Equal dimensions alone are not accepted as proof
of geometry compatibility.  The embedder's declared dimension must match the
lane, and its one returned vector must be one-dimensional with exactly that
dimension.  Vectors are never padded or truncated.  Non-finite and zero-norm
vectors are refused by the established 7G3B numeric validation.

## Query flow

For blank text, `search_text` returns an empty tuple without calling the
embedder or scanning native candidates.  For nonblank text it strips the text,
calls `embedder.embed(normalized_text)` exactly once, and keeps the resulting
vector process-local and ephemeral.  It delegates directly to
`NativeMemoryCompatibilityFacade.search_by_embedding` with the explicit lane
and current text-search filters: `top_k`, `user_id`, `min_score`, and
`type_filter`.  It deliberately does not expose `canon_only`, because the
current `MemoryGraph.search` API does not.

7G3B remains the only implementation of candidate selection, cosine scoring,
filtering, decay, namespace resolution, result projection, current-revision
alignment, READY/USABLE gating, integrity gating, and reconciliation
withholding.  Consequently text results match a direct 7G3B vector search for
the same derived vector, lane, and filters.

## State and failure semantics

No query text or query vector is written to objects, revisions,
representations, payloads, expectations, measurements, operations,
transitions, or reconciliation records.  The adapter grants no authority and
does not execute tools.  Embedder errors, identity mismatch, lane mismatch,
dimension mismatch, and delegated search errors are read-only.

The delegated 7G3B gates mean a stale R1 representation stops participating
when the source advances to R2, then a qualified R2 representation can restore
search.  Later integrity mismatch or another withholding state immediately
removes a representation from results.  Migrated legacy vector evidence with
`UNKNOWN` / reconciliation-required state remains unsearchable even when an
injected embedder matches its geometry; only a genuine native current READY
representation is eligible.

## Deliberate exclusions

There is no query cache, ANN/vector index, vector extension, lexical fallback,
provider factory, provider implementation change, MemoryGraph/Fabric/Character
wiring, live persistence change, dual read/write, production core creation, or
cutover in this phase.  Runtime assembly and any later integration seam remain
Phase 7G4 work.
