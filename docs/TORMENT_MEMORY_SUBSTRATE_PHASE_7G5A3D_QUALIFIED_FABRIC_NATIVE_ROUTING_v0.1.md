# TORMENT Memory Substrate — Phase 7G5A3D

## Qualified Fabric native-routing capability

A3D proves capability, not activation. It introduces a deliberately separate,
explicitly prepared STAGING routing capability for bounded qualification tests.
It does not alter normal Fabric construction or create a backend selector.

```text
NATIVE_ACTIVE = NO
PRODUCTION_NATIVE_ROUTING_DEFAULT = NO
PRODUCTION_NATIVE_ROUTE_READY = NO
```

The pre-existing `NativeMemoryRuntimeBinding` remains an inert facts object.
Its `activation_allowed` fact remains `False`; a binding alone does not route.

## Default path

```text
ordinary Fabric -> legacy MemoryGraph + legacy motif registry
```

No application, environment, CLI, REST, or configuration selector is added.
`app.py`, `router.py`, `character.py`, schema, deployment-state code, and the
runtime-binding activation doctrine are untouched.

## Explicit qualification path

```text
prepared NativeMemoryRuntimeBinding
 + separate NativeFabricRoutingCapability
 + claimed NativeFabricRoutingScope
 + stable native operation key
 + exact Fabric-owned representation lane
 + existing current v1.1 STAGING / LEGACY_ACTIVE core
 -> bounded native route
```

The capability is immutable and retains only core path/identity, routing
scopes, qualified lane facts, and a process-local motif-order owner. It does
not retain a SQLite connection. Each routed operation opens and closes a
fresh, same-thread connection through `open_existing_native_core_connection`.
That opener requires a pre-existing `.db` path and SQLite `mode=rw`, the
qualified runtime, foreign keys, WAL, FULL synchronous mode, busy timeout, and
the current v1.1 schema. It never creates, bootstraps, migrates, or upgrades a
database.

Every routing scope independently validates its memory source namespace,
memory identity namespace, semantic scope, motif alias namespace, motif
identity namespace, membership identity namespace, and idempotency namespace.
The memory and motif alias namespaces must be distinct.

An unclaimed scope remains outside this capability (the future Fabric seam
would preserve ordinary legacy behavior). A claimed scope with no operation
key refuses before opening a native mutation. No random native identity is
generated.

## Native new-memory path

```text
Fabric-owned candidate embedding (canonical float32 C-order bytes)
 -> A3C1 structural translation
 -> process-ordered A3C2 preview and atomic source composition
 -> E1 PENDING
 -> E1 SHA-256 expectation
 -> E1 READY / USABLE
```

The same one-time canonical candidate bytes feed both A3C2's decision witness
and E1 publication. The route never calls an embedder or selects a provider.
If A3C2 commits but E1 is interrupted or publication fails, the source remains
native and retrying the same stable operation key recovers the same source,
motif, membership, and E1 workflow. It never falls back to a legacy write.

Links remain deferred: qualified and raw/unresolved link evidence refuse the
claimed route before source mutation. The unsupported split gate likewise
returns `UNSUPPORTED_NATIVE_SPLIT` before mutation.

## Native reinforcement path

```text
qualified native compatibility embedding search
 -> existing Fabric-owned private policy
    (top_k=3, same agent, raw threshold, class guard, contradiction guard)
 -> A3C3 exact R1/E1 successor and E1 -> E2 continuity
```

The substrate does not own the threshold or contradiction rule. The adapter
receives the Fabric-owned contradiction predicate, keeps shared scopes out of
duplicate reinforcement, and supplies A3C3 the selected exact revision and
representation. Once the A3C3 source operation exists, same-key retry recovers
its durable R1/E1 witness before any new search, allowing E2 recovery without
reselection. The durable retry contract also binds a canonical digest of the
Fabric route facts, so a changed Fabric request under the same operation key
is refused rather than being accepted as the original operation. Tool-result
classification remains structural provenance only and preserves the
no-strength-boost / refresh-timestamp rule.

## Process motif order

`NativeMotifProcessOrder` is keyed by workspace, scope identity, domain, and
motif alias namespace.

```text
first use after process start -> lexicographic current runtime-ID baseline
local A3C2 CREATE             -> append exactly the new runtime ID
ATTACH                         -> order unchanged
next process start             -> lexicographic baseline again
unknown externally added ID    -> fail closed
```

The explicit A3C2 ordered-catalog API preserves this ordering for tie breaks,
while its semantic transaction verifies the same live motif identities and
revisions independent of ordering. `BEGIN IMMEDIATE` plus the catalog witness
remain the durable concurrency protection; the process lock only protects
local order/plan coherence.

## Failure boundary

```text
before claimed native mutation
 -> explicit qualification refusal

after native mutation starts
 -> native failure/retry with the same operation key
 -> NEVER legacy fallback
```

There is no hidden native-to-legacy read fallback, dual write, dual read, or
fabricated `MemoryGraph` entity or motif JSON shadow state.

## Post-write archaeology and bounded completion

The existing code after Fabric's legacy spawn/reinforcement decision was read
before any Fabric seam was considered. Its consumers classify as follows:

| Consumer | Classification | Why A3D does not wire it |
| --- | --- | --- |
| Return construction | B | A bounded native outcome can provide `stored`, `reinforced`, EID, domain, and motifs. |
| Conflict recording | C | Uses legacy graph EIDs and conflict-registry state. |
| SRG collision/writeback | C | Reads and mutates `MemoryGraph` entities and legacy embedding shards. |
| Hivemind emission/evolution | C | Reads legacy graph payloads and writes collective state from legacy source identity. |
| World step | C | Calls `MemoryGraph.step_world`. |
| Character drift/gravity | C | Requires both legacy graph and motif registry. |
| Checkpoints/compression | C | Require legacy graph, registry, and shard snapshots. |
| Proposal novelty, bridges, anchors, motif maintenance | C | Require legacy motif-registry state or legacy derived stores. |
| Fail-soft telemetry/logging | D | Optional, but not a reason to fabricate persistence. |

Accordingly this is intentionally completion level B:

```text
A3D_ROUTING_CAPABILITY = COMPLETE
A3D_QUALIFICATION_GATE = COMPLETE
A3D_PERSISTENCE_ROUTE = COMPLETE
A3D_END_TO_END_FABRIC_ROUTE = BLOCKED
```

`fabric.py` remains unchanged. Wiring an early return around these consumers,
or constructing fake legacy graph/motif state to satisfy them, would either
skip unqualified required behavior or create forbidden shadow authority. The
exact post-write consumers above are deferred to separately ratified bounded
slices.

## Qualified coverage

Focused tests establish existing-core refusal, immutable separate capability
preparation, scope/key/lane refusals, A3C1/A3C2/E1 new memory, source/E1 retry,
native private selection and A3C3 continuity, tool-result behavior, class and
contradiction guards, shared no-reinforcement behavior, link and split
refusals, process ordering, and unknown external motif failure. A3C2 also has
an explicit ordered-catalog regression that proves a process-supplied tie
order can commit while its exact current catalog witness remains valid.

```text
FULL_INGEST_LOST_RESPONSE_REPLAY = NOT_QUALIFIED
DURABLE_BACKEND_OWNERSHIP_SELECTOR = NO
DOMAIN_ROUTER_NATIVE_ROUTING_OPENED = NO
CHARACTER_NATIVE_ROUTING_OPENED = NO
NATIVE_ACTIVE = NO
DUAL_WRITE = NO
DUAL_READ = NO
CUTOVER_OPENED = NO
AUTHORITY_EXPANDED = NO
```
