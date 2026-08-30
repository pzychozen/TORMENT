# TORMENT Memory Substrate — Phase 7G5A3D1

## Fabric post-write runtime boundary

This is a behavior-preserving legacy extraction. It does not make any
downstream subsystem native-aware and it does not wire A3D into Fabric.

Before:

```text
Fabric ingest -> legacy storage decision -> direct legacy post-write consumers
```

After:

```text
Fabric ingest -> legacy storage decision -> FabricPostWriteRuntimePort
             -> LegacyFabricPostWriteAdapter -> same legacy consumers
```

`FabricPostWriteContext` is a frozen, process-local orchestration DTO. It is
not serialized, persisted, or a native operation carrier. Mutable legacy
objects are deliberately separate in `LegacyFabricPostWriteDependencies`; the
adapter receives the exact selected `MemoryGraph`, workspace, motif registry,
and existing Fabric owner/callbacks. It never reloads or reconstructs them.

## Storage outcome classification

```text
NO_WRITE
REINFORCED_EXISTING
CREATED_NEW
```

The classification is produced from the completed legacy storage branch. It
is not inferred later from graph contents and does not alter persistence.

## Actual branch matrix

| Consumer | No write | Reinforced | New memory | Existing gate / behavior |
| --- | --- | --- | --- | --- |
| Contradiction surfacing | No | No | Yes | Private, core, EID; fail-soft. |
| SRG collision/writeback | No | No | Yes | SRG enabled, SRG state, EID; fail-soft. |
| Hivemind packet/evolution | No | No | Yes | Existing created-memory location; enabled, EID, packet flag, governance and coherence gates. |
| Motif maintenance | No | No | Yes | Existing created-memory location; fail-soft. |
| Anchor/refinement/mood calls | No | No | Yes | Existing created-memory location; each fail-soft. |
| World step | Yes | Yes | Yes | Always after the storage decision; fail-soft. |
| Character drift/gravity | No | Legacy no-effect | Yes | Character enabled, stored, periodic, valid seed. The legacy reinforcement path reached its outer gate but had no local `reg`; its enclosing fail-soft boundary produced no effects. This extraction preserves that observed behavior. |
| Checkpoint | Periodic | Periodic | Periodic | Checkpoint enabled and interval; independent of `stored`; fail-soft. |
| Compression / hard cap | Cadenced | Cadenced | Cadenced | Compression enabled and minimum step; independent of `stored`; fail-soft. |
| Proposal | No | Conditional | Conditional | Stored, private, coupling mode, half-life, novelty/rate/signal gates. Its `proposal_id` returns to Fabric unchanged. |
| Bridge suggestion | No | Conditional | Conditional | Stored and the original final-stage random draw. |

The random bridge draw remains in the adapter at its former logical place,
after proposal handling. Clock calls remain inside their respective legacy
helpers rather than being precomputed into the context.

## Preserved execution order and failure topology

For a created memory, the adapter retains:

```text
contradiction -> SRG -> Hivemind -> motif maintenance
-> anchors/refinement/mood -> world step -> Character
-> checkpoint -> compression -> proposal -> bridge -> public return
```

Each prior bounded exception boundary remains local: SRG failure does not stop
Hivemind; Hivemind failure does not stop maintenance; Character failure does
not stop checkpoint; checkpoint failure does not stop compression; compression
failure remains non-fatal; anchors/refinement/mood each remain independently
fail-soft. There is no new adapter-wide catch.

## Native state

```text
NATIVE POST-WRITE ADAPTER = NOT IMPLEMENTED
A3D_NATIVE_ROUTE_WIRED_INTO_FABRIC = NO
NATIVE_ACTIVE = NO
DUAL_WRITE = NO
DUAL_READ = NO
CUTOVER_OPENED = NO
AUTHORITY_EXPANDED = NO
```

This phase creates no persistence, native rows, shadow legacy state, backend
selector, schema change, DomainRouter route, or Character native route. A3D
remains a qualification-only capability, and its end-to-end Fabric route
remains blocked pending separately ratified native post-write adaptation.
