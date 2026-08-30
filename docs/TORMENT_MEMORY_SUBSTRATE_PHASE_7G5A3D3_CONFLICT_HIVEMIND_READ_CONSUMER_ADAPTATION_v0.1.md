# TORMENT Memory Substrate — Phase 7G5A3D3

## Conflict and Hivemind read-consumer adaptation

Status: COMPLETE

This phase makes two legacy post-write consumers independent of the concrete
memory-read backend while preserving the production write route and observable
legacy behavior.

Before A3D3:

```text
conflict surfacing  -> MemoryGraph.search_by_embedding(...)
Hivemind preparation -> graph.entities[eid]
```

After A3D3:

```text
conflict surfacing + Hivemind preparation
        -> PostWriteMemoryReadPort
        -> LegacyPostWriteMemoryAccess (production)

same consumer logic
        -> NativePostWriteMemoryAccess (isolated qualification only)
```

`TormentFabric` constructs `LegacyPostWriteMemoryAccess` from the exact
already-selected `MemoryGraph` and workspace embedding dimension.  It neither
reloads a graph nor opens native storage.  The existing `graph` dependency
remains because SRG and other later post-write consumers are intentionally
still legacy graph-bound.

## Preserved consumer behavior

Conflict surfacing continues to use top-k three, the current agent filter,
self-EID exclusion, core-memory filtering, raw similarity, the existing
conflict detector, and the first qualifying legacy `ConflictRegistry` write.
`ZERO_NORM` is consumed as no candidates before either backend raw search; this
preserves the qualified consumer decision rather than claiming raw backend
zero-query parity.

Hivemind now reads governance and provenance from the structural runtime view,
and resonance/loop facts from its immutable ordinary payload projection.  Its
two legacy-equivalent read/evaluation points remain separate, so a
governance/provenance read failure remains fail-soft and does not change the
later packet flow.  Existing outer gates, coherence threshold, packet shape,
embedding hashing, Character read, SRG context facts, collective-field handoff,
telemetry, and proposal bridge are unchanged.

Native qualification uses only read-only `NativePostWriteMemoryAccess` over
explicit-governance, structurally-provenanced A3C2-compatible memory rows.  It
proves conflict candidate facts and Hivemind admission for ordinary user input,
`non_shareable`, `collective_export_blocked`, and `collective_echo`, including
ordinary `resonance_score` and `loop_type`.  The qualification asserts that
native objects, revisions, representations, operations, transitions,
governance, and provenance counts do not change.

## Deliberate boundaries

**NATIVE ROUTING STILL NOT OPEN.**  There is no native post-write adapter, no
Fabric backend selector, no native persistence wiring, no dual read/write, and
no activation or cutover.

The remaining post-write blockers are grouped by capability:

| Group | Still deferred |
| --- | --- |
| A. Memory enumeration/mutation | Current-memory enumeration, SRG ordering, payload mutation/successor semantics, and reconciliation-sensitive mutation policy. |
| B. Broader runtime graph/motif state | SRG collision state, world stepping, Character graph/motif state, checkpoint/compression, motif maintenance/anchors, and their legacy mutable carriers. |
| C. Already backend-neutral / no longer blocking | Conflict read/search decisions and Hivemind governance, provenance, resonance, and loop read facts. |

This phase does not change authority: governance meaning, collective-echo
separation, proposal approval, and active authorization remain exactly as
before.

## Qualification record

Focused qualification covers legacy conflict cases (ordinary,
similar-noncontradictory, contradictory, non-core, agent-filtered,
zero-norm, and missing candidate), Hivemind structural admission and
fail-soft missing/read-error behavior, and isolated native read-only parity.
The established A3D1 boundary, A3D2 contract/native adapter, legacy conflict,
Hivemind telemetry/collective-echo/governance, ingest response, and native
routing/memory composition/reinforcement suites remain the regression gates.
