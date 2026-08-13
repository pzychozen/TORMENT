# Core / MemoryGraph Archaeology Closure — 2026-08-13

**Scope:** `CORE_MEMORYGRAPH_ARCHAEOLOGY_V1`

Core / `MemoryGraph` is closed for this archaeology pass.

## Authority model

| Artifact | Authority / role |
|---|---|
| `nodes.jsonl` | Canonical node authority; append-only; the last record per EID is current canonical state. |
| Embedding shards, row maps, manifest | Canonical embedding artifacts. |
| `edges.jsonl` | Canonical edge ledger; not node-reconstruction authority. |
| `memory_events.jsonl` | Canonical event ledger; not node-reconstruction authority. |
| SQLite | Optional, derived, rebuildable sidecar. |
| `MemoryGraph.entities` / `world.entities` | Derived runtime state. |
| Embedding RAM cache/matrix | Derived runtime state. |
| Physics trails / trajectory live state | Ephemeral/diagnostic unless separately logged. |

## Graph identity model

EIDs are graph-local, not globally unique.

- Private graph identity: `workspace + agent + eid`
- Shared graph identity: `workspace + domain + eid`

Raw EID alone is insufficient cross-graph identity.

## Restart result

`CORE_RESTART_EQUIVALENCE_SUPPORTED` is scoped to the `MemoryGraph` substrate.

The archaeology proved that canonical nodes, embedding references, and stored edges
survive restart; restart EID allocation derives from canonical state; SQLite is
disposable/rebuildable; RAM physics/cache differences are expected; and an
unflushed spawn does not become a recovered canonical node. This is not a claim of
crash-atomic durability.

## Repairs

### B1 — SRG targeting

A shared/private graph-local EID collision could cause SRG writeback to land in
the wrong graph because raw EID resolution was private-first. The repair uses
origin-aware graph resolution, fails closed for inconsistent, unknown, or deep
origins, and has no raw-EID fallback.

**NO SRG FORMULA OR TUNING CHANGE.**

**WRITEBACK_ACTIVATION_UNCHANGED.**

`B1_TARGETING_ONLY`: this did not repair or alter SRG recursion itself.

### B2 — Fabric close ownership

`TormentFabric.close()` now closes Fabric-owned private/shared `MemoryGraph`
instances so shard memmaps are released deterministically, especially on Windows.
No memory-authority semantics changed.

### B3 — trajectory rebuild

Derived SQLite trajectory rebuild now consumes current daily trajectory logs while
retaining legacy `trajectories.jsonl` compatibility. Normal retrieval and canonical
node authority are unaffected.

### Gate-A security classification

`_resolve_srg_writeback_target` is a `LEGITIMATE_NEW_TRACKED_SURFACE`: selecting
where an existing write lands is authority-significant even though the helper is
non-mutating. The Gate-A heuristic was not weakened or bypassed.

## Embedding-space invariant

Production `Workspace` enforces persisted embedding-space compatibility through
`workspace_meta.json` and its `embed_dim` / provider / model lock. A bare
`MemoryGraph` does not enforce this independently; production Fabric does.

## Regression evidence

```text
Core Phase-2 harness:                 13 passed
Gate-A writer/fan-out inventory:      13 passed
Broad ordinary non-Brainvision suite: 5865 passed, 5 skipped
```

Brainvision remains in its own research lane because its isolation/repository
assumptions are incompatible with this combined Core regression invocation. Its
tests were not removed or weakened.

## Parked, non-blocking terrain

The following remain recorded without blocking Core closure:

- same-EID source-lineage/revision terrain;
- unflushed-spawn / ingest non-transactionality;
- JSONL no-fsync / crash-durability fragility;
- `test_workspace_isolation.py` lifecycle fixture debt;
- trajectory rebuild processed-count over-report on daily/legacy overlap;
- pre-existing `_hit_eid` exception-logger edge case;
- legacy payloads lacking scope/domain fail closed for B1 writeback.

## Handoff

**Next subsystem:** `Shared / Hive / Collective`

Carry forward: raw EID is not global identity, and the workspace embedding lock
exists at the Workspace/Fabric layer.
