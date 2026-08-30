# TORMENT Memory Substrate — Phase 7G5A3D7

## Remaining post-write state topology and cutover-blocker freeze

Status: archaeology and characterization complete. Production remains on the
legacy Fabric path. This phase adds no native post-write adapter, selector,
schema change, migration, or route activation.

Starting point: `5e3902812bca6f6ea5f3edf55aa88211b656bb88`.

## Ruling

The remaining tail is not one `MemoryGraph` compatibility problem.

1. Identity-anchor creation/retirement and mood-drift creation are default
   derived-memory operations: they create or revise durable core-memory truth.
2. `SeedWorld` is a process-local kinematic overlay invoked after every ingest
   result. Its stepped coordinates are not durable core-memory truth.
3. Character and compression are optional compound features with narrowly
   identifiable read, successor, and external-store needs.
4. Suggestions, bridges, CharacterState, checkpoints, and trajectory artifacts
   remain side-store or diagnostic state; native memory selection does not make
   them native core-memory authority.

The known broad `requires MemoryGraph` classification is retired for these
consumers. Qualified conflict, Hivemind, and SRG collision are not reopened.

## Evidence vocabulary and available primitives

| Class | Meaning |
| --- | --- |
| A | durable memory truth |
| B | durable motif truth |
| C | process-local runtime state |
| D | authoritative side-store state |
| E | derived/rebuildable state |
| F | non-authoritative snapshot, cache, or diagnostic state |
| G | external/deep-memory store |

| Primitive | Current scope |
| --- | --- |
| `NativePostWriteMemoryAccess` | read-only current memory, ordered enumeration, compatibility embedding read/search; no mutation or legacy cache-vector projection |
| `NativeMotifRuntimeReader` | read-only current native motif geometry and ordered memberships |
| A3C2 composition | one compound memory + motif + membership publication; cannot replace a legacy derived writer that intentionally creates no motif membership |
| A3C3 + A3D6 | reinforcement and its narrowly authorized SRG effective-overlay contribution; not a general payload-successor operation |

## Motif state

`update_entropy_and_suggest(auto_merge=False)` logs `MOTIF_ENTROPY` and may
append `MOTIF_MERGE_SUGGESTED` events and persist `motif_merges.json`. It does
not rewrite `motifs.json` or memberships. Entropy is E/F; suggestions are D
workflow state.

With `auto_merge=True`, the same function approves eligible suggestions. It
rewrites the kept motif centroid/members/agents/strength, deletes the dropped
motif, writes `motifs.json`, and records approval. That is B durable motif
truth. A future extension of `MotifRuntimePort` must preserve this split rather
than hiding a merge behind suggestion maintenance.

## Complete consumer classification

Every row executes after ordinary storage. Therefore no listed failure rolls
that storage branch back.

| Consumer | Execution gate | Inputs | Outputs / mutations | Authority, durability, restart | Failure topology | Existing port / native primitive / legacy carrier | SRG relevance | Severity | Future boundary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Motif entropy / suggestions | `CREATED_NEW`, registry and policy; auto-merge false by default | per-domain motif geometry/strength, policy | entropy event; suggestion records | E/F entropy plus D suggestions; JSON reloads | own fail-soft block; anchors continue | legacy `MotifRuntimePort` method; native reader only; registry owns merge files/events | none | OPERATIONAL_PARITY_BLOCKER | extend `MotifRuntimePort` with named maintenance/suggestion semantics |
| Motif automatic merge | same, with policy `auto_merge_motifs=true` and thresholds | current motif geometry and suggestions | rewrites motifs/members; approves suggestion | B+D; JSON reloads | same fail-soft block | native reader only; composition primitives do not perform merge | none | CONDITIONAL_FEATURE_BLOCKER | `MOTIF_RUNTIME_MUTATION` |
| Identity-anchor emission | `CREATED_NEW`, repeated local members, role/gap gates | selected graph payloads, motif members/label, role store, seed overlap, embedder, anchor state | new `identity_anchor` memory and embedding; anchor state; audit dirty | A+D; row and state reload; native EID aliases are compatible identities | own fail-soft block; refinement/mood continue | no neutral writer; A3C2 is not parity-safe because legacy anchor creates no membership; graph + anchor JSON | new initial row only | HARD_ROUTE_BLOCKER | `DERIVED_MEMORY_MUTATION`: typed no-motif create plus side-state update |
| Identity-anchor refinement / retirement | `CREATED_NEW`, matching active anchor rows | full payload scan, graph order, environment thresholds | full-payload successors setting retirement/supersession fields | A; successor records reload | own fail-soft block; mood continues | read views only; A3D6 is SRG contribution inside A3C3, not generic successor; graph carrier | successor must include effective SRG/collision if present | HARD_ROUTE_BLOCKER | `DERIVED_MEMORY_MUTATION` general authorized full-payload successor |
| Mood-drift emission | `CREATED_NEW`, non-neutral affect, default-on mood flag, confidence/change/gap | classifier result, `affect_state.json`, embedder, graph | latest affect state even with no row; qualifying transition creates `mood_drift` row/history | A+D; row/history reload | own fail-soft block | no neutral writer; A3C2 would add unwanted motif; graph + affect JSON | new initial row only | HARD_ROUTE_BLOCKER | `DERIVED_MEMORY_MUTATION` with explicit no-motif creation and idempotency design |
| World stepping | all outcomes | live `SeedWorld` entities | advances live position, velocity, trail, histories | C; stepped overlay is lost at restart | fail-soft; later consumers run | no port/native primitive; world and graph entity objects | none | HARD_ROUTE_BLOCKER | `PROCESS_LOCAL_WORLD_STATE` source-bound overlay |
| Trajectory logging / classification | every world step; classify every 50 | live positions/velocities/histories | V2 genesis/frame/chunk/manifest or legacy JSONL; `TRAJ_CLASSIFY` event; live label | C+F; artifacts persist but do not restore world or durable node labels | inside fail-soft world step | no port; V2 writer/legacy logger/events are carriers | none | OPERATIONAL_PARITY_BLOCKER | world overlay plus `NON_AUTHORITATIVE_SNAPSHOT_PARITY` evidence lifecycle |
| Character drift measurement | Character flag, stored, periodic, seed; effectively `CREATED_NEW` only | graph insertion order; type/user/half-life/`born_step` payload; normalized `_emb_by_eid` cache; motif centroid/seed fallback; prior state | read-only drift report/tier counts | C+E; report is transient until state save | silent outer failure | native ordered views/raw embeddings exist, but no legacy cache-vector projection; graph/registry carrier | none | CONDITIONAL_FEATURE_BLOCKER | `MEMORY_DERIVED_RUNTIME_READERS` exact cache-normalization/payload/order contract |
| Character state persistence | after successful effective measurement | drift report, CharacterState | `character_state.json`, 50-entry history | D; independent JSON reloads; only `seed_id`, no memory revision ID | swallowed by Character outer boundary | `CharacterStore` remains valid; native EID aliases suffice for seed fallback | none | NOT_A_ROUTE_BLOCKER | retain `CharacterStore` unchanged |
| Character gravity correction | effective high `away_seed` drift | seed text, embedder, drift info, graph, motif registry | new canon `drift_correction` row; optional motif attach/create; flush | A+B; durable row/motif | silent Character failure | A3C2 is related compound capability but no Character route exists | new initial row only | CONDITIONAL_FEATURE_BLOCKER | `DERIVED_MEMORY_MUTATION` composed with motif primitive only where legacy attaches |
| Checkpoint creation | checkpoint flag (default true), positive periodic step | ModelState, monitor/context, CharacterState, motif summary, legacy shard manifest | bounded checkpoint JSON | F snapshot of C/D/E; missing/corrupt load returns none; no core authority | component failures become none; outer failure logs/continues | helpers exist; no native primitive; shard-manifest path is legacy carrier | none | OPERATIONAL_PARITY_BLOCKER | `NON_AUTHORITATIVE_SNAPSHOT_PARITY`; never fabricate native shard snapshot |
| Compression trigger detection | compression flag (default false), minimum step | `tri_mod`, EventDetector process history, current count | transient trigger/cooldown state | C; resets at restart | enclosing compression block suppresses | native enumeration can count, current code reads graph | none | NOT_A_ROUTE_BLOCKER | small count read within `MEMORY_DERIVED_RUNTIME_READERS` |
| Compression candidate reads/scoring | compression trigger or hard cap | full payload, entity `born_step`, motif coherence projection | transient candidates/routes | C+E; recomputed | enclosing block suppresses | native view has payload but not entity `born_step`; native motif reader geometry but no coherence projection; graph/file path carriers | must see effective current payload | CONDITIONAL_FEATURE_BLOCKER | `MEMORY_DERIVED_RUNTIME_READERS` with only proven added fields |
| Compression short path | enabled, selected short candidate | current full payload, score/tier | full-payload successor reducing strength and setting compression fields | A; successor reloads | per-candidate retained | no generic native successor; A3D6 is SRG-only inside A3C3 | successor must preserve effective SRG/collision | CONDITIONAL_FEATURE_BLOCKER | `TYPED_MEMORY_SUCCESSORS` |
| Compression long path | enabled, selected long candidate | current payload, embedding, score/tier, deep store | deep export first, then core successor marking export/reducing strength | G then A; independent stores persist | export failure means no core patch; core-patch failure leaves export with no compensation | embedding read exists; no deep-store port/transaction; graph/shard/deep store carriers | deep export sees live payload before successor; successor retains effective SRG | CONDITIONAL_FEATURE_BLOCKER | `EXTERNAL_DEEP_MEMORY` + `TYPED_MEMORY_SUCCESSORS` |
| Hard-cap compression | inside enabled compression; count above cap | same read/score/route/deep inputs, min age overridden | same short/long effects and event log | C/A/G/F; same restart rules | enclosing block suppresses | no separate native primitive | same as route selected | CONDITIONAL_FEATURE_BLOCKER | reuse compression boundaries |
| Proposal creation | stored private row, propose/sync coupling, half-life, policy, registry | immutable post-write context, identity overlay, policy, registry, embedding | proposal side-store record; identity save; proposal ID | D; independent persistence | uncaught: prevents bridge/reply after storage | all inputs are context/side stores; no graph/native provider | none | NOT_A_ROUTE_BLOCKER | retain existing proposal/identity stores and returned ID |
| Bridge suggestion | stored and random chance | all-domain motif geometry, `tri_mod` threshold | `bridges.json` suggestion and event | D workflow + E geometry-derived; reloads independently; no motif/memory mutation | uncaught: prevents reply after previous effects | no cross-domain port; native reader provides per-domain geometry; BridgeRegistry carrier | none | OPERATIONAL_PARITY_BLOCKER | `MOTIF_CROSS_DOMAIN_GEOMETRY_READ` with existing BridgeRegistry |

### Character measurement freeze

- Entity iteration is graph insertion order.
- Seed canon is skipped; agent filtering is exact; tier counts increment before
  the recency test.
- Recency reads `payload["born_step"]` (default zero), not `created_at` or
  `SeedEntity.born_step`.
- The measurement reads only `graph._emb_by_eid`. MemoryGraph owns float32
  cache normalization with its existing `norm + 1e-12` rule; no embedding is
  loaded at measurement time.
- Seed geometry is the current motif centroid, then cached seed-EID mean, then
  the recent average. Distance is `1 - cosine(avg, seed)`; previous-state
  direction uses strict `0.03` threshold.

A3D7 locks this behavior, including its surprising `born_step` rule. It does
not repair it.

### World restart freeze

`spawn_memory` serializes initial `pos`, `vel`, and `vel0`. `step_world`
changes `SeedEntity.pos`, `SeedEntity.vel`, trails, and histories without a
node write. Classification changes the live payload label but only writes a
lightweight event. V2 close seals a trajectory tail; a restart reloads the
initial node payload, not the latest coordinates or classification label.

World is analogous to SRG in being process-local, but differs materially: it
has no qualified successor materialization and trajectory evidence is
observability, not a restartable overlay.

### Checkpoint component ruling

| Component | Authority and native disposition |
| --- | --- |
| step, ModelState, monitor, runtime context, character modulation | F snapshot of process-local kernel state; equivalent snapshot may exist later, never memory authority |
| CharacterState | F copy of D `CharacterStore` state; leave the side store authoritative |
| motif summary | F derived summary; native route may build a read-only equivalent later |
| embedding shard snapshot | F legacy-shard metadata; native SQLite must not fabricate it |

`load_latest_checkpoint` returns `None` for corrupt/missing JSON and does not
mutate memory. Current Fabric imports checkpoint save helpers only; it does not
call checkpoint load/restore as a native-memory recovery source.

## Post-write execution matrix

`Y` means the consumer reaches its own gate. `effective` distinguishes an
outer gate reached from a real behavior.

| Consumer | NO_WRITE | REINFORCED_EXISTING | CREATED_NEW | Native identity | Transient state | Failure / FabricPostWriteOutcome |
| --- | --- | --- | --- | --- | --- | --- |
| entropy / suggestions | no | no | Y | motif IDs | no | fail-soft; no outcome |
| automatic merge | no | no | policy Y | motif IDs/revisions | no | fail-soft; no outcome |
| anchor emission | no | no | Y | new anchor ID | no | fail-soft; no outcome |
| anchor refinement | no | no | Y | successor ID | effective SRG if any | fail-soft; no outcome |
| mood drift | no | no | affect Y | new mood ID | affect state | fail-soft; no outcome |
| world | Y | Y | Y | physical entity mapping | Y | fail-soft; no outcome |
| trajectory | with world | with world | with world | physical entity mapping | world history | fail-soft; no outcome |
| Character measure | no | outer gate, not effective | periodic/seed effective Y | seed aliases | cached vectors/prior state | silent; no outcome |
| Character state | no | no effective write | after measure Y | no revision ID | no | silent; no outcome |
| gravity | no | no effective branch | high drift Y | new row/motif IDs | drift report | silent; no outcome |
| checkpoint | periodic Y | periodic Y | periodic Y | optional summary IDs | kernel context | fail-soft; no outcome |
| compression trigger/scoring | feature Y | feature Y | feature Y | candidates | detector/coherence | fail-soft; no outcome |
| compression short | selected Y | selected Y | selected Y | successor ID | effective payload | retained on error; no outcome |
| compression long | selected Y | selected Y | selected Y | core/deep IDs | payload/embedding | retained on error; no outcome |
| hard cap | enabled/count Y | enabled/count Y | enabled/count Y | same as compression | same | fail-soft; no outcome |
| proposal | no | policy Y | policy Y | none | no | uncaught; proposal ID is only outcome field |
| bridge | no | chance Y | chance Y | motif IDs | random draw | uncaught; no outcome field |

The legacy Character reinforcement oddity is intentionally frozen: its outer
periodic stored gate is met, but the inner `CREATED_NEW` condition causes no
measurement, state write, gravity, or reflex behavior.

## Characterizations added

`tests/test_a3d7_post_write_state_topology.py` locks:

1. stepped world coordinates/classification are live while node bytes remain
   unchanged; restart restores initial kinematics and no node label;
2. suggestion-only entropy preserves `motifs.json` while auto-merge rewrites
   motif truth;
3. compression exports before core patch, export failure prevents that patch,
   and core failure does not compensate an already-exported deep record;
4. Character drift uses cached embeddings and payload `born_step` rather than
   `created_at`;
5. corrupt checkpoint loading returns `None` without mutation; and
6. bridge suggestion persists without motif mutation.

## Minimal future partition

1. `PROCESS_LOCAL_WORLD_STATE` — live source-bound world overlay, then its
   trajectory evidence lifecycle. Default hard blocker.
2. `DERIVED_MEMORY_MUTATION` — typed no-motif derived-memory creation and
   general authorized full-payload successors, including exact effective SRG
   contribution where present. Default hard blocker.
3. `MEMORY_DERIVED_RUNTIME_READERS` — exact Character/compression reader
   facts: order, cache normalization, effective `born_step`, coherence.
4. `MOTIF_RUNTIME_MUTATION` — separate suggestion maintenance from actual
   merge mutation.
5. `EXTERNAL_DEEP_MEMORY` — preserve export-before-core/no-compensation while
   composing with typed successors.
6. `NON_AUTHORITATIVE_SNAPSHOT_PARITY` — checkpoints and trajectory reporting,
   without fabricated shard state.
7. `MOTIF_CROSS_DOMAIN_GEOMETRY_READ` — bridge suggestion geometry while
   BridgeRegistry remains the side-store owner.

This is capability-oriented: no separate Character, anchor, bridge, or
compression storage system is justified.

## Routing gate reassessment

There are **2 hard blocker groups** before a native post-write adapter can be
qualified for default Fabric behavior:

1. `PROCESS_LOCAL_WORLD_STATE`.
2. `DERIVED_MEMORY_MUTATION`.

Default operational parity remains for motif suggestions, trajectory evidence,
checkpoints, and bridge suggestions. Character is conditional on a configured
seed despite its environment flag defaulting true. Compression/hard-cap is
conditional on the default-false compression flag, and automatic merge is
policy conditional. Proposal handling is not a native-memory route blocker.

```text
A3D7_REMAINING_POST_WRITE_TOPOLOGY = FROZEN

SRG_BLOCKER_GROUP = COMPLETE
CONFLICT_MEMORY_BLOCKER = COMPLETE
HIVEMIND_MEMORY_BLOCKER = COMPLETE

POST_WRITE_CONSUMERS_RECLASSIFIED = YES
MOTIF_STATE_CLASSIFIED = YES
CHARACTER_STATE_CLASSIFIED = YES
WORLD_STATE_CLASSIFIED = YES
CHECKPOINT_STATE_CLASSIFIED = YES
COMPRESSION_STATE_CLASSIFIED = YES
PROPOSAL_STATE_CLASSIFIED = YES
BRIDGE_STATE_CLASSIFIED = YES
ANCHOR_STATE_CLASSIFIED = YES

HARD_ROUTE_BLOCKER_GROUP_COUNT = 2
DEFAULT_REQUIRED_BLOCKER_GROUPS = PROCESS_LOCAL_WORLD_STATE, DERIVED_MEMORY_MUTATION
OPTIONAL_FEATURE_BLOCKER_GROUPS = MEMORY_DERIVED_RUNTIME_READERS, MOTIF_RUNTIME_MUTATION(auto_merge), EXTERNAL_DEEP_MEMORY, TYPED_MEMORY_SUCCESSORS(compression)
OPERATIONAL_PARITY_BLOCKERS = MOTIF_SUGGESTION_MAINTENANCE, TRAJECTORY_EVIDENCE, CHECKPOINT_SNAPSHOTS, BRIDGE_SUGGESTIONS
NON_BLOCKING_CONSUMERS = PROPOSAL_CREATION, CHARACTER_STATE_STORE, COMPRESSION_TRIGGER

NEXT_IMPLEMENTATION_PARTITION = PROCESS_LOCAL_WORLD_STATE -> DERIVED_MEMORY_MUTATION -> MEMORY_DERIVED_RUNTIME_READERS -> MOTIF_RUNTIME_MUTATION -> EXTERNAL_DEEP_MEMORY -> NON_AUTHORITATIVE_SNAPSHOT_PARITY -> MOTIF_CROSS_DOMAIN_GEOMETRY_READ

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
