# TORMENT Memory Substrate — Phase 7G3A Relationship Compatibility v0.1

## Scope

Phase 7G3A adds a native-only compatibility primitive for a relationship between two
already committed compatibility memories. It deliberately does not change
`MemoryGraph`, Fabric, Character, legacy JSONL files, or live persistence wiring.
It is available only on a qualified STAGING core and has no production-core or
cutover implication.

The public boundary is `NativeMemoryCompatibilityFacade.create_memory_relationship`:

```python
create_memory_relationship(
    source_legacy_source_namespace_id=..., source_eid=...,
    target_legacy_source_namespace_id=..., target_eid=...,
    idempotency_namespace_id=..., idempotency_key=...,
    identity_namespace_id=..., semantic_scope_id=...,
    relationship_kind="LINK", weight=..., legacy_timestamp=...,
    extra_payload=..., governance_state="UNKNOWN",
)
```

All UUID namespace and scope arguments are explicit. Both endpoint aliases are
resolved as `legacy source namespace + EID -> native object ID`; a bare EID is
never globally resolved. Each resolved object must be the admitted compatibility
core-memory carrier (`LEGACY_CORE_NODE`). Unknown aliases and aliases to another
object kind fail before a semantic operation can publish. A `MemoryDraft` token is
not an EID and is rejected before publication.

Only the canonical compatibility kind `LINK` is accepted in this slice. The
relationship itself has explicit semantic scope, while endpoint scopes come from
the committed source and target revisions and may differ. Endpoints are always
`SOURCE` and `TARGET`, with `IDENTITY` binding and no bound revision ID. Advancing a
source memory from R1 to R2 therefore does not retarget or revise an existing link.

The optional `get_memory_relationship` projection reverses endpoint IDs through
the caller-supplied source and target namespaces. It fails rather than inventing an
EID if either scoped reverse alias is absent or ambiguous.

## Bounded current link contract

The bounded check covered `MemoryGraph.spawn_memory`, its edge load/abort handling,
and the direct Fabric/Character/Promotion callers. The current legacy API declares
`links: Optional[List[str]]`; `spawn_memory` loops each raw target and appends:

```python
{"src": int(ent.eid), "tgt": tgt, "kind": "link", "w": float(strength), "ts": _now_ts()}
```

`src` is an integer EID. `tgt` is normally a string identifier (and is unvalidated,
so the persisted population may be mixed) because `KernelSignals.links` is passed
unchanged; it is not reliably a scoped EID. No conversion is guessed by this
primitive. The direct edge-dictionary persistence/read behavior
found is confined to `MemoryGraph`: it appends to `edges.jsonl`, reloads that file
into `MemoryGraph.edges`, and drops only the live source-edge view on an unflushed
abort while retaining JSONL residue. Fabric’s direct relationship to this file in
the bounded surface is inventory/copy handling and its existing pre-flush abort
path; no external load-bearing dictionary reader or query ordering rule was found.

Append order is retained by the legacy list/file, but no semantic meaning for edge
order was established by the bounded callers. Legacy spawn does expose an in-memory
edge and JSONL residue before `flush_node`; that deferred pre-flush workflow cannot
be made drop-in safe from the native primitive and is intentionally not adapted.

## Native translation and durability

Successful publication uses the existing `NativeRelationshipService` semantic
transaction path. It creates a logical relationship UUID, immutable R1, complete
typed endpoint aggregate, current relationship pointer, a native
`RELATIONSHIP_REVISION` transition, a relationship-revision effect, and an
operation output. This supplies H1 (current pointer), H2 (typed effect), H5
(immutable relationship revision and endpoints), and H8 (output equals the actual
published relationship result). No legacy admission record, edge mirror, event, or
JSONL access is created.

Weight is stored only as finite numeric relationship payload (`weight`). An optional
legacy timestamp is stored as informational `legacy_timestamp`; it is not native
commit-time or ordering evidence. The relationship has
`authority_category="NOT_APPLICABLE"`; `authority`, authorization, scope,
lifecycle, governance, identity, endpoint, revision, transition, operation, weight,
and timestamp shadows are rejected from flexible payload. Persisting a LINK never
grants active authorization.

The caller supplies stable idempotency namespace/key. An identical retry reconstructs
the same operation, relationship, R1, and transition. A changed source/target alias,
kind, weight, scope, or payload under the same idempotency identity conflicts. There
is intentionally no endpoint-based global uniqueness: distinct operation identities
may create independent LINK relationships with the same endpoint pair.

## Explicit deferrals

- `spawn_memory(..., links=...)` compatibility adaptation and pre-flush publication;
- generic compatibility relationship patch/successor support;
- `edges.jsonl` read, write, mirroring, admission, or dual-write;
- MemoryGraph/Fabric/Character/embedding-store wiring;
- embedding or text search (7G3B/7G3C);
- reconciliation/H6, migrations, production core creation, and cutover.

`COMPAT_LINKS_DROPIN_SUPPORTED = NO`.
`COMPAT_RELATIONSHIP_PATCH_SUPPORTED = NO`.
`COMPAT_SEARCH_BY_EMBEDDING_SUPPORTED = NO`.
`COMPAT_TEXT_SEARCH_SUPPORTED = NO`.
`DUAL_WRITE_IMPLEMENTED = NO`.
