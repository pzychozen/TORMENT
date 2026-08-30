# TORMENT Memory Substrate — Phase 7G5A3D6

## Typed transient SRG successor materialization

Status: qualified in isolation. Production remains on the legacy Fabric path.

Schema remains v1.2 before and after this phase. No persistent SRG carrier or
v1.3 migration is introduced.

## Ruling

Legacy collision remains a process-local live-payload mutation. It does not
write JSONL at the collision site. When a separately legitimate legacy caller
later invokes `MemoryGraph.update_payload()`, that routine serializes the
entire current live payload. Thus its next JSONL record includes both that
caller's ordinary fields and any effective live `srg` / `srg_collision` values.

The native equivalent is not a standalone “materialize SRG” revision,
operation, or transition. A typed snapshot can be supplied only to an already
authorized successor semantic transaction:

```text
durable R1 + exact effective transient overlay + legitimate successor patch
    -> one durable R2
```

The initial consumer is A3C3 reinforcement. It publishes its ordinary R2,
R2 governance, source transition and source output exactly as before; where an
overlay is present, its `source_state.payload` additionally contains the
typed `srg` and, when present, `srg_collision` contribution. E1 bytes are
then carried unchanged to E2 through the pre-existing A3C3 representation
workflow. No-overlay A3C3 canonical intent remains byte-for-byte shaped as it
was before this phase: no materialization key is added.

## Typed exact-current snapshot

`SRGSuccessorMaterialization` carries only:

```text
predecessor_revision_id
predecessor_revision_ordinal
effective_srg_state
effective_collision_report (optional)
canonical_digest
```

The digest canonically binds all five facts. The snapshot contributes only
`srg` and `srg_collision`; it is not a generic payload patch. A3C3 checks the
predecessor at plan preparation and again inside its semantic transaction.
Any stale predecessor fails closed before publication. A changed snapshot
under a reused source idempotency key changes the durable retry contract and
therefore conflicts rather than silently recovering a different source.

When present, the snapshot is in the durable A3C3 source intent's
`retry_contract`. This permits a response-lost retry to recover the same R2
after a new connection has been opened. A successful caller acknowledgement
then consumes the matching in-process overlay; source failure before R2
leaves it in place. A process restart has a new owner and therefore has no
overlay to materialize.

## Process ownership and connection boundary

`NativeSRGProcessState` owns only in-memory overlays and exact current
revision witnesses, keyed by native core, legacy source namespace and EID. It
does not own a SQLite connection, path, selector, storage handle, or
authority. `NativeSRGTransientRuntime` is the short-lived adapter that binds
one already-open qualified connection to this process owner.

The prepared A3D routing capability owns one such process owner. A collision
can therefore occur under one connection, the connection can close, and the
next qualified duplicate-reinforcement route can open a new connection and
consume the overlay into its one R2. A response lost after R2 but before
acknowledgement recovers R2/E2 from the stored A3C3 intent and only then
consumes the matching overlay. It never creates R3.

## Legacy serialization inventory

`MemoryGraph.update_payload()` mutates the selected live entity and appends
the entire resulting payload to `nodes.jsonl`; it does not itself alter
embedding bytes or motif membership. `flush_node()` likewise serializes the
whole live payload. The reviewed current callers are classified below.

| Caller family | Classification / whole-payload result | SRG / other live facts | Embedding, motif, deep-memory facts | Future materialization fit |
| --- | --- | --- | --- | --- |
| Fabric ordinary duplicate reinforcement (A3C3 counterpart) | `FULL_LIVE_PAYLOAD_SERIALIZATION` through `update_payload` | serializes `srg`, `srg_collision`, strength/count/timestamps and every other current payload field | update itself changes neither embedding bytes nor motif state | qualified here |
| Compression short path | `FULL_LIVE_PAYLOAD_SERIALIZATION` through `update_payload` | serializes both SRG fields plus compression metadata and all other live payload fields | update itself changes neither embedding bytes nor motif state | future consumer |
| Compression long path | `FULL_LIVE_PAYLOAD_SERIALIZATION` through `update_payload` | serializes both SRG fields plus compression metadata | deep export receives the current live payload before the later update; update itself changes neither embedding bytes nor motif state | future consumer; deep export may also need the effective SRG view |
| Identity-anchor retirement/refinement | `FULL_LIVE_PAYLOAD_SERIALIZATION` through `update_payload` | serializes both SRG fields plus anchor lifecycle fields | update itself changes neither embedding bytes nor motif state; surrounding anchor code may have separate motif work | future consumer |
| Fabric private reinforcement and baton lifecycle updates | `FULL_LIVE_PAYLOAD_SERIALIZATION` through `update_payload` | serializes both SRG fields plus their ordinary fields | update itself changes neither embedding bytes nor motif state | future consumer |
| Spine governance update and migration provenance update | `FULL_LIVE_PAYLOAD_SERIALIZATION` through `update_payload` | serializes both SRG fields plus governance/provenance payload fields | update itself changes neither embedding bytes nor motif state | future consumer |
| Collective re-ingest direct mutation followed by `flush_node` | `FULL_LIVE_PAYLOAD_SERIALIZATION` through whole-payload flush | serializes both SRG fields plus directly changed live payload data | that site separately manages its own embedding metadata; flush itself changes neither embedding bytes nor motif state | future consumer |
| New-memory initial flush, character seed/gravity flush, promotion flush | `NEW_MEMORY_INITIAL_FLUSH` | whole initial payload is serialized, but a predecessor collision overlay does not exist in the normal topology | initial creation owns its own embedding/motif behavior | no predecessor materialization topology |

No reviewed caller requires a generic materialization patch or a separate SRG
publication. Compression, anchor, re-ingest, promotion, and all remaining
future callers remain unadapted by this phase.

## Qualification coverage

Focused tests establish:

- legacy live-payload characterization: a later `update_payload()` record
  contains ordinary reinforcement fields plus effective `srg` and
  `srg_collision`;
- no-overlay A3C3 intent and results remain unchanged;
- overlay A3C3 creates exactly one R2 and one normal E2 with E1/E2 byte
  continuity, without a standalone SRG carrier;
- source failure after provisional R2 insertion rolls back and retains the
  overlay;
- a process-owned overlay survives the close of its original core connection;
- a fresh router connection materializes it in the qualified duplicate R2;
- response-loss interruption after source, E2 pending, and E2 expectation
  each recovers R2 rather than creating R3, then consumes the overlay; and
- a fresh process owner exposes only the durable payload baseline, while the
  same committed native route key recovers the durable R2/E2 result without
  requiring the lost overlay.

```text
A3D6_SRG_SUCCESSOR_MATERIALIZATION = COMPLETE
LEGACY_SRG_REINFORCEMENT_MATERIALIZATION = QUALIFIED
NATIVE_SRG_REINFORCEMENT_MATERIALIZATION = QUALIFIED
SRG_REINFORCEMENT_MATERIALIZATION_PARITY = PASS
NATIVE_SRG_PROCESS_OWNER = QUALIFIED
NATIVE_SRG_STATE_SURVIVES_CONNECTION_BOUNDARY = PASS
NATIVE_SRG_STATE_SURVIVES_PROCESS_RESTART = NO
SRG_MATERIALIZATION_CREATES_STANDALONE_REVISION = NO
SRG_MATERIALIZATION_CREATES_STANDALONE_OPERATION = NO
SRG_MATERIALIZATION_CREATES_STANDALONE_TRANSITION = NO
A3C3_NO_OVERLAY_PARITY = PASS
A3C3_OVERLAY_SUCCESSOR_PARITY = PASS
A3C3_OVERLAY_LOST_RESPONSE_RECOVERY = PASS
A3C3_E1_E2_BYTE_CONTINUITY_WITH_OVERLAY = PASS
SRG_MATERIALIZATION_GOVERNANCE_CHANGED = NO
SRG_MATERIALIZATION_PROVENANCE_CHANGED = NO
SRG_MATERIALIZATION_AUTHORITY_EXPANDED = NO
SRG_SUCCESSOR_MATERIALIZATION_CONTRACT = QUALIFIED
SRG_SUCCESSOR_MATERIALIZATION_READY = YES
SRG_TRANSIENT_OVERLAY_MATERIALIZATION_READY = YES

COMPRESSION_MATERIALIZATION_CONSUMER_REWIRED = NO
ANCHOR_MATERIALIZATION_CONSUMER_REWIRED = NO
DEFAULT_FABRIC_BEHAVIOR_CHANGED = NO
NATIVE_ACTIVE = NO
DUAL_WRITE = NO
DUAL_READ = NO
CUTOVER_OPENED = NO
AUTHORITY_EXPANDED = NO
NATIVE_POST_WRITE_ADAPTER = NO
A3D_NATIVE_ROUTE_WIRED_INTO_FABRIC = NO
A3D_END_TO_END_FABRIC_ROUTE = BLOCKED
```
