# Phase 7G1 Compatibility Read Contract

The current `MemoryGraph` surface is EID-oriented: `entities[eid]` exposes an
entity payload; `spawn_memory`, `update_payload`, and `flush_node` write legacy
state; `search` combines embedding generation, vector retrieval, filters, and
ranking. 7G1 supports none of those write or search operations.

Supported: `NativeMemoryCompatibilityFacade.resolve_memory_eid`, scoped reverse
EID lookup, current memory read, exact native revision read, and immutable
`LegacyMemoryView.to_legacy_dict`. Every lookup requires a legacy source
namespace and EID. EID is an alias, never a native object or revision ID.

The view is read from the native object's selected current immutable revision.
Lifecycle, governance, authority, scope, and provenance come from structural
native columns; flexible payload supplies only domain content. The facade is
native-only: it opens no JSONL files and has no legacy fallback, shadow store,
dual read, dual write, execution decision, or vector-search surface.

Deferred: 7G2 compatibility writes (`spawn_memory`, `update_payload`,
`flush_node`, edges) and 7G3 search/representation behavior. MemoryGraph and
Fabric remain unchanged; current runtime JSONL authority remains unchanged;
there is no cutover.
