# TORMENT Memory Substrate — Phase 9D I4A

## Post-write cognition dependency system fit

**Status:** FROZEN I4AFF ARCHITECTURE / IMPLEMENTATION NOT STARTED
**Scope:** architecture and code archaeology only; this memo authorizes no production migration, activation, retirement, or formula change.

## Decision

The normal private agent ingest writer is a composition point, not a single durable transaction. Its canonical memory commit occurs at `graph.flush_node`, after spawn, best-effort embed-audit dirty marking, immediate in-memory motif attachment/creation, and pre-flush symbol/resonance enrichment, and before the post-write fan-out. I4 must preserve that topology and each consumer's independently established failure disposition. A native post-write implementation must therefore select source-compatible adapters and bind existing external durable owners; it must not turn the flow into one SQLite-owned writer or assert generic exactly-once delivery.

```text
SEMANTIC_ADAPTER_OWNERSHIP != DURABLE_STORE_OWNERSHIP
LEGACY_POST_WRITE_RETIREMENT = NO
POST_WRITE_FORMULA_CHANGES_REQUIRED = NO
```

## I4 matrix denominator extraction

I4AFF freezes the preservation matrix at 76 live capabilities: 72 initially enumerated capabilities plus embed-audit dirty marking, Character drift reflex, SRG last-ingest-band coupling, and SRG relational EMA. The exact I4 architecture set below contains 40 matrix row names. The count expands the matrix's explicit I4 clusters where a cluster expressly names a sub-row: motif live order names the three motif/order rows, and the SRG successor path names its query mutation, process-local cross-route state, post-write state, and restart rows. It also includes the existing failure/read rows needed to preserve post-write effects. No live capability is left without a matrix disposition.

| # | Exact matrix row name | I4 relationship / boundary |
|---:|---|---|
| 1 | Input write gate / provenance | Before canonical commit; admission, provenance, identity, baton and write gate. |
| 2 | Memory create | Canonical commit branch. |
| 3 | Reinforcement | Canonical update branch. |
| 4 | Motif attach / create | Before canonical commit for a newly created memory. |
| 5 | Motif maintenance / split / merge | After commit created-memory consumer. |
| 6 | Ordering / top-k truncation | Motif context/order witness; live creation must append. |
| 7 | Active motif context | Pre-write context and post-write motif consumer input. |
| 8 | Conflict persistence | After commit, created private core memory only; fail soft. |
| 9 | Conflict query read | Later query consumer of conflict evidence. |
| 10 | SRG query mutation / breathing | Query-side evolved state; same-entity successor interaction is policy-sensitive. |
| 11 | SRG post-write collision / state | After commit, created SRG state; fail soft. |
| 12 | Restart / recovery | Process restart loses unsaved query mutation/overlay unless later same-entity write serializes it. |
| 13 | Character seed/context | Pre-write seed/context composition; loading is fail soft. |
| 14 | Character drift | After commit, due private stored write; CharacterStore owner. |
| 15 | Character gravity | After drift decision; graph/motif/embedding geometry; fail soft. |
| 16 | Role / affect | Role precommit best-effort external state; affect classification/payload provenance. |
| 17 | Derived memory | Created-memory post-write consumers; independently fail soft slots. |
| 18 | World / trajectory | Always attempted after primary outcome; post-commit fail soft. |
| 19 | Checkpoint | Periodic post-world snapshot; post-commit fail soft. |
| 20 | Bridge suggestions | Last post-write step; may propagate after primary commit. |
| 21 | Hivemind / collective context | Governance/read context used by collective emission. |
| 22 | Hivemind emission / convergence | Created stored eligible memory; append external packet; fail soft. |
| 23 | Archive recall | Separate retrieval read route, not normal ingest fan-out. |
| 24 | Archive retrieval-count write | Separate retrieval read-route side effect; fail soft. |
| 25 | Shared ingest | Direct shared path with governance scope; distinct from private proposal flow. |
| 26 | Proposals | Post-commit private proposal submission; may propagate. |
| 27 | Compression / deep-memory export | Periodic automatic post-write work; fail soft; external deep owner. |
| 28 | Deep memory / spirit return | Query lane consumes deep output; enabled profile without parity refuses activation. |
| 29 | Failure dispositions | Cross-cutting parity requirement; do not normalize. |
| 30 | Archive document lifecycle | Separate trusted archive public operations. |
| 31 | Index rebuild | Separate maintenance/public operation. |
| 32 | Promotion operations | Separate archive-to-memory operator/public operation. |
| 33 | Reference lifecycle | Independent reference ingest/load lifecycle. |
| 34 | Environment lifecycle | Independent evidence-validated environment lifecycle. |
| 35 | Baton lifecycle | Normal private ingest admission plus separate resolution lifecycle. |
| 36 | Closure lifecycle | Independent proposal/ratify/commit/revise lifecycle. |
| 37 | Embed-audit dirty marking | Best-effort workspace audit write after spawn and before motif/flush; it may survive a failed primary commit. |
| 38 | Character drift reflex | Rising-edge process state plus optional external callback; shares the Character outer fail-soft boundary. |
| 39 | SRG last-ingest-band coupling | Ingest writes a per-agent process-local band; query and trace consume it for the existing same-band multiplier. |
| 40 | SRG relational EMA | Ingest seeds/updates a per-agent process-local EMA; Spine consumes it in later geometric context. |

```text
I4_MATRIX_ROWS_TOTAL = 40
FUNCTIONALITY_MATRIX_DENOMINATOR = 76
UNMAPPED_LIVE_CAPABILITIES = 0
```

`Workspace maintenance / clone jobs` remains a public-maintenance matrix capability, but is not in the ordinary writer sequence nor the matrix's explicit I4 ordinary-ingest cluster.  It remains preserved outside an I4 post-write migration slice.

## Actual normal production ingest and post-write graph

The ordinary route is `/agent/ingest` in `torment_service/app.py`, which constructs a Spine ingest request with an idempotency key.  `SpineRequest.submit_task` performs routing/trust/preflight and dispatches `_fast_ingest`; while holding the agent lock it invokes `Fabric.ingest(..., public_mutation_key=idempotency_key)`.

```text
/agent/ingest
  -> SpineRequest(operation=ingest, idempotency key)
  -> Spine.submit_task: route/trust/native-facade preflight
  -> Spine._fast_ingest under fabric.locks.agent_lock
  -> Fabric.ingest
       1. Refuse candidate-shaped text before cognition.
       2. Prepare legacy public-mutation fingerprint (legacy storage does not
          give it R1 replay semantics).
       3. Select workspace/identity; compose provenance.
       4. Load Character badge/context best effort; validate baton.
       5. kernel.process; mutate agent state; build/process-local SRG band/EMA.
       6. RoleStore load/update/save best effort; affect classification best effort.
       7. Embed/dimension-check; rank domain; preflight domain MotifRegistry;
          choose graph and write gate; assemble PreparedFabricIngest.
       8. NO_WRITE: return context with no primary storage, then run the
          always post-write path with its established guards.
       9. REINFORCE: find duplicate and update legacy graph payload/strength,
          subject to guards; a broad duplicate-path exception falls through
          to CREATE rather than declaring a transactional reinforcement failure.
      10. CREATE: graph.spawn_memory; best-effort mark existing embed audit dirty;
          MotifRegistry.attach_or_create;
          compute coherence/symbol/resonance; best-effort symbol side state
          and in-memory entity enrichment.
      11. CANONICAL COMMIT: graph.flush_node(entity).
          Failure aborts the unflushed node and returns canonical commit
          failure; deliberately retained precommit embedding/event/edge
          residue is reconciled later.
      12. For a stored outcome, construct LegacyFabricIngestStorageAdapter,
          FabricPostWriteContext, LegacyPostWriteMemoryAccess and
          LegacyFabricPostWriteDependencies, then run LegacyFabricPostWriteAdapter.
             CREATED_NEW:
               a. contradiction surface / ConflictRegistry
               b. SRG collision/state
               c. Hivemind emission/convergence
               d. motif entropy/suggestions, then derived slots
             every context:
               e. world step
               f. Character drift then Character gravity when due
               g. periodic checkpoint
               h. automatic compression/deep export
               i. proposal submission
               j. bridge suggestions (last)
```

This is the actual order, not a desired order.  In particular, canonical `flush_node` precedes the adapter and some immediate motif mutation precedes the flush.  The `allow_write = false` outcome still reaches the adapter's always-run world/Character/checkpoint/compression/proposal/bridge calls, whose own guards decide whether an effect is applicable.

## Commit and external-owner map

| Boundary | Effects and durable/runtime owner |
|---|---|
| Before canonical memory commit | Admission/provenance and kernel/agent process state; RoleStore write (best effort); affect classification; graph spawn; best-effort existing embed_audit.json dirty write; MotifRegistry attach/create; and best-effort symbol-state/payload enrichment. A motif mutation can therefore precede a failed flush; attachment errors are not normalized by a surrounding create catch. |
| Canonical memory commit | CREATE commits through legacy selected-graph `flush_node`; REINFORCE commits through legacy graph `update_payload`. They are intentionally asymmetric. |
| After canonical commit, in-process adapter | ConflictRegistry; SRG graph state/overlay; Hivemind/collective packet state; MotifRegistry maintenance; derived-memory services; world graph/trajectory; CharacterStore and gravity graph/motif geometry; checkpoint file; compression/deep-memory store; ProposalRegistry; BridgeRegistry. |
| Separate read route | ArchiveStore recall and retrieval-count mutation after core query; conflict, SRG and deep reads consume their respective state. |
| Later async/operator/public operation | Archive document lifecycle, promotion, manual compression/spirit/deep operations, index rebuild, reference/environment/baton/closure lifecycles.  These are not normal post-write durable effects. |

External ownership is preserved: CharacterStore owns Character durable state; ConflictRegistry owns conflict records; BridgeRegistry owns bridge suggestions; RoleStore and affect/symbol side state retain their current ownership; ProposalRegistry owns proposal state; world graph/SRG owns trajectory and SRG state; checkpoint owns its atomic snapshot file; Hivemind owns collective packets/convergence; ArchiveStore owns archive state and retrieval counters; and the deep-memory/compression owner retains exported material.  Native adapters may orchestrate these owners but do not subsume them.

## Failure-disposition and replay map

| I4 effect group | Relative to primary commit | Legacy disposition / later detectability | Replay and partial-state rule |
|---|---|---|---|
| Input gate, provenance, memory create | Before / at commit | Refusal stops storage; flush failure reports a non-stored outcome. Preflush event/edge/embedding residue may remain for reconciliation. | Do not auto-replay a failed canonical outcome as if no work occurred. |
| Embed-audit dirty marking | After spawn, before motif/flush | If an audit file exists, it is atomically rewritten dirty; all errors are suppressed. A successful dirty write survives a later flush failure. | Value-level re-marking is idempotent, timestamp is not; no operation key exists. |
| Reinforcement | At primary update | Duplicate branch is broadly caught and can fall through to CREATE; no atomicity guarantee is evidenced for partial update. | Preserve exact reinforcement-attempt disposition; do not claim exact-once. |
| Motif attach/create | Before flush | Attach failure raises without Fabric abort; successful attachment followed by flush failure leaves motif mutation untouched while abort removes only graph live state. | Recovery needs an explicit residue witness/policy, not a silent sort, reattach, or rollback. |
| Conflict, SRG collision, Hivemind, motif maintenance, derived slots | After stored create | Each adapter path catches/logs/suppresses; primary memory remains.  Later conflict/SRG/collective/derived reads can observe absence where applicable. | Best effort; a replay can duplicate or change an external result unless that owner provides its own dedupe. |
| World, Character drift/gravity/reflex, checkpoint, automatic compression | After primary outcome | Each is guarded and broadly suppressed. World is attempted for all contexts; Character's drift/gravity/reflex share one outer suppression boundary; the rest have stored/schedule/enable guards. | Best effort; restart does not establish a post-commit outbox. Reflex rising-edge process state resets at restart. Checkpoint write itself uses temp+replace, but automatic failure remains suppressed. |
| Proposal and bridge suggestions | After primary commit | Proposal submission has no enclosing adapter catch; BridgeRegistry errors intentionally propagate.  The primary memory stays durable while caller can receive error. | Do not retry blindly: a partially successful external proposal/bridge may already exist. |
| Archive recall/count, promotion, index, reference/environment/baton/closure | Separate route/operation | Route-specific errors and idempotency apply; archive count increment is suppressed. | Preserve each public operation's own replay rules, not ingest receipt rules. |
```text
FAILURE_DISPOSITION_PARITY_REQUIRED = YES
POST_WRITE_OUTBOX_OR_GLOBAL_TRANSACTION = NOT_EVIDENCED
```

The current native public-mutation receipt lifecycle applies to public ingest: an already complete matching receipt returns its recorded result; a `COGNITION_STARTED` receipt without a prepared state is refused for recovery rather than automatically rerun.  It does not prove generic post-write replay, exactly-once external delivery, or recovery for all effects.

## Row-level semantic, mathematical, durable, and runtime ownership

“Legacy graph” below means the current selected graph/durable memory owner, not a destination for a migration. A dash means the row is a lifecycle or policy capability with no separate mathematical formula evidenced in this trace.

| Matrix row | Semantic / mathematical owner | Durable owner | Runtime / routing owner |
|---|---|---|---|
| Input write gate / provenance | Fabric ingest admission, provenance and identity semantics | Selected legacy graph/audit state where stored | Fabric ingest via Spine fast ingest |
| Memory create | Fabric create semantics; existing kernel/reinforcement/motif mathematics | Selected legacy graph through flush_node | Fabric ingest/storage adapter |
| Embed-audit dirty marking | Workspace embedding-health invalidation semantics | Existing workspace embed_audit.json only when present | Fabric/derived creation helper |
| Reinforcement | Fabric duplicate/reinforcement mathematics | Selected legacy graph payload | Fabric ingest/storage adapter |
| Motif attach / create | MotifRegistry motif mathematics | MotifRegistry | Fabric create path |
| Motif maintenance / split / merge | MotifRegistry and existing split policy | MotifRegistry | Legacy motif post-write runtime |
| Ordering / top-k truncation | Motif runtime ordering semantics | MotifRegistry / recovered motif state | Motif context projection |
| Active motif context | MotifRegistry context semantics | MotifRegistry | Fabric prepare and motif runtime |
| Conflict persistence | Conflict detection semantics | ConflictRegistry | Post-write contradiction surface |
| Conflict query read | Conflict query composition | ConflictRegistry | Existing query composition |
| SRG query mutation / breathing | Existing SRG mathematics | Legacy live payload when later serialized; current native overlay is process-local | Query and SRG runtime |
| SRG post-write collision / state | Existing SRG collision mathematics | SRG/graph state | Post-write SRG collision runtime |
| Restart / recovery | SRG persistence semantics | Persisted graph payload / native receipt only where applicable | Startup/recovery and same-entity writes |
| Character seed/context | Character seed/context mathematics | CharacterStore | Fabric pre-write composition |
| Character drift | Character drift equations | CharacterStore | Character drift post-write runtime |
| Character drift reflex | Rising-edge callback semantics | Process-local Fabric map; external callback owner | Character post-write runtime |
| Character gravity | Character gravity equations and graph geometry | Legacy graph/MotifRegistry plus CharacterStore inputs | Character gravity post-write runtime |
| Role / affect | Role inference and affect classification semantics | RoleStore and existing affect/symbol side state | Fabric pre-write composition |
| Derived memory | Identity anchor/refinement/mood-drift semantics | Respective derived-memory owners | Derived post-write runtime |
| World / trajectory | World stepping mathematics | World graph / trajectory state | LegacyWorldRuntime post-write call |
| Checkpoint | Checkpoint snapshot contract | Checkpoint file/store | Checkpoint runtime and manual public route |
| Bridge suggestions | Existing stochastic bridge policy | BridgeRegistry | Last post-write bridge runtime |
| Hivemind / collective context | Governance, coherence and collective eligibility semantics | Hivemind / collective owner | Collective context and query composition |
| Hivemind emission / convergence | Packet, convergence and proposal-bridge semantics | Hivemind / collective owner | Hivemind post-write runtime |
| Archive recall | Archive retrieval semantics | ArchiveStore | Retrieve read route |
| Archive retrieval-count write | Archive count semantics | ArchiveStore | Retrieve read route after archive retrieval |
| Shared ingest | Shared governance/trust semantics | Shared legacy scope/owner | Public shared ingest route |
| Proposals | Proposal eligibility/submission semantics | ProposalRegistry and identity state | Post-write proposal runtime |
| Compression / deep-memory export | Existing compression/deep export semantics | Deep-memory/compression owner | Automatic post-write runtime; separate manual operation |
| Deep memory / spirit return | Spirit-return query semantics | Deep-memory owner | Query spirit lane / explicit deep routes |
| Failure dispositions | Per-effect legacy failure semantics | The owner named by the affected row | Adapter boundary and public route |
| Archive document lifecycle | Archive lifecycle semantics | ArchiveStore | Trusted archive public endpoints |
| Index rebuild | Index maintenance semantics | Existing index owner | Public/maintenance operation |
| Promotion operations | Archive promotion semantics | ArchiveStore plus selected memory graph when promoted | Public promotion operation |
| Reference lifecycle | Reference linkage and audit semantics | Reference store and audit ledger | Reference ingest/load routes |
| Environment lifecycle | Evidence validation semantics | Environment source-of-truth and ledger | Environment routes |
| Baton lifecycle | Baton status/event semantics | Baton/legacy graph state | Normal private ingest plus baton resolution |
| Closure lifecycle | Proposal/ratify/commit/revise semantics | Closure/proposal event stores | Closure public lifecycle |

## Dependency findings by semantic cluster

### Create/reinforce is the first native prerequisite

Every downstream post-write consumer needs a truthful primary-outcome witness. This is an architectural requirement, not a proposed production class:

~~~text
scope = private | shared
attempt_origin = direct_create | reinforcement_attempt
reinforcement_disposition =
  reinforced | semantic_fallthrough_to_create | exception_fallthrough_to_create | not_applicable
final_storage_outcome = CREATED_NEW | REINFORCED_EXISTING | NO_WRITE | REFUSED
create_failure_disposition = motif_attach_failure_raised | canonical_flush_failure_structured | not_applicable
committed_primary_state = YES | NO
eid / qualified identity when applicable
step, schedule, selected scope/domain, and route/public-receipt witness when applicable
~~~

Reinforcement is private-only; shared reinforcement is unreachable. Tool-result reinforcement suppresses the strength boost, increments reinforcement_count, sets last_reinforced and timestamp, sets last_tool_refresh_ts for tool-result rows, and backfills direct-ingest provenance only when old provenance is missing. Cross-class and contradiction guards deliberately select semantic fallthrough to CREATE; any duplicate-path exception selects exception fallthrough to CREATE. CREATED_NEW gates contradiction, SRG collision, Hivemind emission, motif maintenance, and derived consumers. Character drift first requires stored, then resolves seed state before its REINFORCED_EFFECTIVE_NOOP result. Proposal requires stored/private/coupling/half-life policy. World is attempted for every context. Checkpoint and compression require independent enable and step interval guards. Bridge policy is last and retains caller-visible error behavior.

The first slice must expose this outcome without changing existing create, reinforcement, kernel, motif, Character, or SRG equations.

### Motif write dependency and ordering witness

Create performs spawn, best-effort embed-audit dirty marking, attach/create, coherence/symbol/resonance computation, best-effort symbol-state/payload enrichment, and then flushes the primary node. Post-commit motif maintenance updates entropy and suggestions; derived consumers run after its attempt, even when maintenance itself failed softly. Auto split policy is a separate existing MotifRegistry concern and is not permission to change a threshold or mutation ordering.

~~~text
PERSISTED / RECOVERED ORDER = lexical
LIVE POST-LOAD CREATION ORDER = append / creation order
~~~

A native parity slice must carry an explicit live motif insertion-order witness (or equivalent faithful registry state) for newly created motifs after load. It may use lexical recovered order only at recovery/projection where legacy does. It must not sort the live registry, infer order from a lexical durable view, or invent a new ordering rule.

### Conflict is a post-commit, fail-soft external write

The contradiction surface runs only for a newly created private core memory with an entity id. It searches current embeddings, skips self and non-core candidates, detects conflict, and adds the evidence to the ConflictRegistry. Its broad catch logs at debug and suppresses the error, leaving the canonical memory durable. The later query conflict lane consumes that registry evidence; absence after a suppressed failure is therefore observable as absent conflict context. The smallest slice is an adapter call with the existing ConflictRegistry, create/private/core gates, candidate filters, and suppression disposition—never a ConflictRegistry migration.

### Character, role/affect, and derived state are independent effects

Character seed/context is broad fail-soft pre-write composition. Character drift is due only when enabled, primary memory is stored, the step is positive, and step modulo drift_every is zero; shared scope returns not-applicable before loading a seed. Missing seed is unavailable. After seed availability, reinforcement returns REINFORCED_EFFECTIVE_NOOP, whereas a private create may persist measured CharacterStore state when it passes legacy drift criteria. Character gravity follows a high-drift decision and calls existing gravity correction with graph, MotifRegistry, embedder, seed, agent, step, and drift result. That correction is a nested canonical-memory write: spawn, motif interaction (whose attach error is internally debug-suppressed), and flush. Drift, gravity, and reflex share one outer catch-all suppression boundary.

The reflex is separate from measurement and gravity. After measured drift, Fabric reads and updates the process-local key (workspace_id, agent_id) in _last_drift_was_high. Only a high result with a prior false value invokes the optional external drift_reflex_callback. The map is constructed empty, is not checkpointed, and clears on restart; the first observed high state after restart may re-fire the callback. Callback failure is logged inside the shared outer Character boundary. Its later semantic effect belongs to the callback owner, not CharacterStore.

RoleStore load/update/save is best-effort before primary commit and its external role file can survive a later primary commit failure. Affect classification is best effort and contributes the in-memory payload tag/confidence and, only on successful classification, its attribution envelope; no independent normal-ingest affect side store was observed. Those payload facts disappear when the spawned entity is aborted after a failed flush. Symbol/resonance state is different: its agent side-state file is saved before flush inside its own best-effort boundary, can survive a later flush failure, and is consumed by later ingest composition. The derived runtime has distinct identity-anchor, anchor-refinement, and mood-drift calls, each independently caught. Identity/refinement are shared no-ops; mood drift may still run. They must not be collapsed into one all-or-nothing Character/derived transaction.

### SRG successor write policy and query-to-ingest composition

The frozen I3C result establishes:

~~~text
query breathing = live-payload mutation
restart without later same-entity write = lost
later same-entity legacy write = serializes evolved state
current native overlay = process-local only
~~~

Post-write collision runs only for a new state with an entity id and enabled SRG. It evaluates current memories and finite embeddings against the existing threshold, applies collision state when matched, and suppresses errors. The required composition loop is:

~~~text
query -> process-local breathing overlay -> later same-entity ingest
  -> collision scanner reads effective_srg_state
  -> overlay affects collision decision
  -> collision may mutate incoming and existing SRG state
  -> later query behavior changes
~~~

I4AF ratifies this successor policy:

~~~text
SRG_QUERY_BREATHING_STORAGE = PROCESS_LOCAL
SRG_QUERY_BREATHING_CONSEQUENCE = MAY_AFFECT_POST_WRITE_COLLISION
SRG_OVERLAY_PREDECESSOR_BINDING = EXACT_REVISION
NO_OVERLAY = write proceeds
OVERLAY_LOST_ON_RESTART = absent, matching legacy
CURRENT_OVERLAY_PLUS_SAME_ENTITY_SUCCESSOR = carry into successor canonical payload
STALE_PREDECESSOR = refuse successor write precommit
INCONSISTENT_OR_UNPROVABLE_OVERLAY_READ = refuse with a distinct precommit reason
QUERY_TAIL_BREATHING_WRITEBACK_FAILURE = FAIL_SOFT
SAME_ENTITY_SUCCESSOR_OVERLAY_MATERIALIZATION_FAILURE = FAIL_CLOSED_PRECOMMIT
~~~

The binding is the exact core, semantic scope/source namespace, EID, and predecessor revision. Native process-state overlay ownership remains in NativeSRGTransientRuntime; native reinforcement and typed derived-anchor lifecycle are the two presently wired successor-materialization flows. The policy does not authorize their activation or extend materialization to uncovered paths.

### World, trajectory, and checkpoint are ordered but separately owned

After created-only consumers, LegacyWorldRuntime advances the world by calling graph step_world with the existing classification/logging cadence for every adapter context. Character drift/gravity/reflex follows. The checkpoint is then considered only when checkpointing is enabled, step is positive, and the checkpoint interval divides the step. The checkpoint assembles motif summary/shard and Character state best effort and snapshots model, corridor monitor, kernel runtime context, Character state, motif summary, and shard state; it does not capture SRG. A gravity-generated nested memory can therefore affect motif state before the checkpoint snapshot. The checkpoint store writes a temporary file then atomically replaces the destination; its automatic post-write wrapper suppresses errors. Manual checkpoint save is a separate operator route. I4E must preserve this ordering and ownership; it must not make a failed periodic snapshot roll back world or memory.

### Shared ingest, proposals, bridges, collective, deep, and archive remain distinct

Direct shared ingest is a governed scope and is not a proposal materialization shortcut. Hivemind packet emission is a created/stored/entity-id path gated by collective enablement, governance/nonshareable/export checks, collective-echo rules, and coherence at least 0.15; it appends an external packet and may attempt convergence/proposal bridging under nested soft failure. It does not create a third native memory scope.

Proposal submission is a private stored post-write path with propose-or-sync coupling, half-life, proposal-allowed policy, registry submit, and identity save. It has no general adapter catch. Bridge suggestions are stochastic through existing tri-modifiers and the bridge-suggestion runtime; BridgeRegistry errors intentionally propagate even though primary memory is already committed. Query-side bridge peek is out of this post-write scope and remains covered by query preservation.

Automatic compression checks its existing enable/minimum-step conditions and may run compression/hard-cap logic; it suppresses failure. Deep-memory export remains owned externally. An enabled deep profile without native parity must refuse activation, and spirit return remains a separate query/retrieval concern. Archive document ingest/read/delete is ArchiveStore-owned public functionality. During retrieve, archive recall is attempted after core query and archive retrieval-count increment is independently fail-soft. Promotion, index rebuilding, manual compression, and explicit deep/spirit operations are separate public/operator flows, not normal ingest tail calls.

Reference, environment, baton, and closure retain their separate lifecycles: reference linkage is validated before store and repeat loads make new load events; environment validates evidence before its source-of-truth store and has best-effort ledger audit; a baton is admitted through normal private ingest but resolves with its own consumption/event semantics (already consumed is a no-op); closure separately proposes, ratifies, commits, and revises without automatic enactment.

## Required idempotency, replay, and reconciliation contract

| Effect | Required parity posture | Crash/restart / partial success treatment |
|---|---|---|
| Canonical create/reinforce | Preserve current public receipt result where it exists; preserve outcome witness and canonical entity identity. | Matching COMPLETE receipt returns its recorded result. COGNITION_STARTED with no prepared state is recovery-required/refused, not auto-rerun. |
| Motif immediate mutation | No invented exactly-once guarantee. Preserve order witness and reconciliation visibility. | A failed flush can leave precommit motif/embedding/event/edge residue; recovery must be explicit and must not silently reorder motifs. |
| Conflict, SRG collision, Hivemind, motif maintenance, derived | Best effort, owner-local dedupe only if existing owner provides it. | A crash after canonical commit can omit the side effect; retry is not generically safe and later reads may see absence. |
| World, Character, checkpoint, automatic compression | Best effort with their existing guards/schedules. | Do not introduce a global outbox. A later retry may not be semantically equivalent because step, state, and schedule have advanced. |
| Proposals and bridges | Preserve post-commit propagation and owner behavior. | Treat as potentially partial external success. Do not blanket retry; require owner-specific idempotency/reconciliation evidence. |
| Archive count and public lifecycle operations | Route-specific existing semantics. | Archive count is independently fail-soft. Promotion, index, reference, environment, baton, and closure retain their individual public operation idempotency/no-op rules. |
| SRG query state | Policy review before any native successor-write behavior. | Process-local overlay may disappear on restart today. No unreviewed durable replay or overlay serialization. |

The required native implementation interface is therefore a durable primary-outcome witness plus source-selected post-write adapters and external-owner binders. It is not a generic delivery queue:

~~~text
IDEMPOTENCY_REPLAY_REQUIREMENTS =
  receipt parity for public primary ingest where established
  + precise primary outcome and entity witness
  + per-owner failure disposition parity
  + explicit reconciliation for precommit residue / postcommit absence
  + no invented exact-once or automatic replay guarantees
~~~

## Initial I4A implementation sequence — superseded by I4AF

All slices are design proposals only. Each retains the legacy writer/adapters and all external owners. No slice licenses production activation or retirement.

### I4B — Primary outcome, immediate motif truth, and failure witness

**Input invariants:** existing admission/provenance, kernel and reinforcement mathematics, selected graph/domain, public receipt semantics, and live motif registry behavior are unchanged.

**Matrix rows:** Input write gate / provenance; Memory create; Reinforcement; Motif attach / create; Motif maintenance / split / merge; Ordering / top-k truncation; Active motif context; Failure dispositions.

**Code-owner seam:** Fabric prepare/storage outcome contract, the native public ingest executor/storage adapter, the source-selected motif runtime adapter, and the existing MotifRegistry. No owner transfer.

**Required implementation/test gates:**

- Characterize CREATE, REINFORCE, NO_WRITE, REFUSE, and canonical-flush-failed outcome witnesses.
- Assert that all created-only consumers are skipped for reinforcement while the always-run path preserves its own gates.
- Test a post-load live motif creation sequence against the explicit append-order witness; separately retain lexical recovered order.
- Test a failed flush retaining only the established reconcilable precommit residue; do not assert invented rollback.
- Prove same complete public receipt behavior and uncertain cognition-started recovery refusal.

**Claude review point:** verify that outcome categories and motif witness do not silently imply transactional rollback, lexical live ordering, or new idempotency.

**Retirement consequence:** none. Legacy graph storage, MotifRegistry, and post-write adapter remain live.

### I4C — Conflict, Character, role/affect, and derived owner composition

**Input invariants:** I4B outcome witness, existing private/shared/core gates, current graph geometry, embedding inputs, Character equations, and external stores are preserved.

**Matrix rows:** Conflict persistence; Conflict query read; Character seed/context; Character drift; Character gravity; Role / affect; Derived memory; Failure dispositions.

**Code-owner seam:** source-selected contradiction, Character, role/affect, and derived adapters calling ConflictRegistry, CharacterStore, RoleStore, and existing derived owners. Query conflict composition remains the qualified query implementation.

**Required implementation/test gates:**

- Create/private/core conflict only; self/non-core filtering; external registry evidence; debug-suppressed error with retained primary memory.
- Character schedule truth: disabled, shared, missing seed, reinforcement effective-no-op, due private create, gravity applied/not-applied, and broad suppression.
- Role load/update/save and affect provenance retain precommit best-effort disposition.
- Test each derived slot independently, including shared identity/refinement no-op and mood-drift eligibility.
- Verify later query sees the same owner-produced absence/presence rather than a copied SQLite shadow.

**Claude review point:** adversarially inspect gate order, Character seed/drift/gravity separation, and whether any source adapter accidentally changes a formula or makes soft failure transactional.

**Retirement consequence:** none. ConflictRegistry, CharacterStore, RoleStore, and derived services remain durable owners.

### I4D — SRG successor composition with world, trajectory, and checkpoint

**Input invariants:** I4B storage/entity witness, existing SRG mathematics and collision threshold, current world step cadence, checkpoint snapshot contract, and external world/checkpoint ownership.

**Matrix rows:** SRG query mutation / breathing; SRG post-write collision / state; Restart / recovery; World / trajectory; Checkpoint; Failure dispositions.

**Code-owner seam:** source-selected SRG post-write adapter, LegacyWorldRuntime, checkpoint runtime/store, and the existing query overlay facade. No global graph transaction.

**Required implementation/test gates:**

- Post-commit SRG collision only for the existing eligible new-state/entity case; preserve its suppressing failure path.
- Deliberately test query breathing, restart without same-entity write, and later same-entity write separately.
- Test world-before-Character/checkpoint ordering and checkpoint interval/enable guards; assert snapshot contains the currently contracted kernel, Character, motif, shard, model, and corridor state.
- Test automatic checkpoint failure as non-rollback, plus independent manual checkpoint route.

**Claude review point (hard blocker):** approve a written policy for native same-entity successor behavior: fidelity-preserving overlay serialization, explicit refusal when fidelity is unavailable, or a precisely justified legacy-loss disposition. No implementation/activation chooses among these alternatives before review.

**Retirement consequence:** none. SRG, world graph, checkpoint store, and query overlay remain intact.

### I4E — Shared/proposal/bridge/collective post-commit semantics

**Input invariants:** storage scope truth, governance/trust rules, private/shared policy, coherence value, coupling/half-life policy, and existing stochastic bridge modifiers remain unchanged.

**Matrix rows:** Shared ingest; Proposals; Bridge suggestions; Hivemind / collective context; Hivemind emission / convergence; Failure dispositions.

**Code-owner seam:** existing shared route, ProposalRegistry, BridgeRegistry, Hivemind/collective owner, and source-selected post-write adapters.

**Required implementation/test gates:**

- Direct shared ingest remains distinct from proposal submission and materialization.
- Hivemind gates: stored/create/entity, enablement, governance/nonshareable/export/echo policy, and coherence threshold; nested convergence failure remains soft.
- Proposal owner submission preserves its caller-visible propagation after primary commit.
- Bridge suggestion remains last, stochastic under the existing modifiers, and preserves BridgeRegistry propagation after the canonical memory is durable.
- Assert there is no third native memory scope and no collective-owner migration.

**Claude review point:** verify every governance and error boundary, especially caller-visible proposal/bridge errors after a durable primary memory.

**Retirement consequence:** none. ProposalRegistry, BridgeRegistry, and Hivemind remain owners and legacy routes remain available.

### I4F — Deep, archive, and independent public lifecycle boundaries

**Input invariants:** external deep/archive/index/reference/environment/baton/closure ownership and existing route-specific policy/error semantics remain unchanged.

**Matrix rows:** Compression / deep-memory export; Deep memory / spirit return; Archive recall; Archive retrieval-count write; Archive document lifecycle; Index rebuild; Promotion operations; Reference lifecycle; Environment lifecycle; Baton lifecycle; Closure lifecycle; Failure dispositions.

**Code-owner seam:** automatic compression adapter; deep-memory owner; ArchiveStore and retrieve/public routes; existing index/promotion/reference/environment/baton/closure services. They are bound, not absorbed.

**Required implementation/test gates:**

- Compression schedule/hard-cap gates and soft failure; deep export remains external.
- Enabled deep profile plus no parity produces activation refusal; query spirit return stays distinct from export.
- Core query before archive recall; archive count increment separately soft; document lifecycle and promotion remain public operations.
- Reference linkage/load-event behavior, environment evidence validation and ledger best effort, baton consumed no-op, and closure's separate proposal/ratify/commit/revise outcomes.
- Index rebuild remains maintenance/public work, not an ingest tail.

**Claude review point:** prevent accidental absorption of external/archive/deep state into native SQLite and verify no public lifecycle becomes an unreviewed ingest side effect.

**Retirement consequence:** none. ArchiveStore, deep owner, and all public lifecycle services remain active.

## I4AF corrections — outcome residue, SRG census, and corrected sequence

This section supersedes the earlier slice grouping in this memo. It does not authorize implementation.

### Primary causal order and orphan-motif residue

~~~text
precommit:
  admission/provenance -> kernel/SRG process state
  -> RoleStore best effort -> affect classification best effort
  -> embedding/domain/write gate

reinforcement attempt:
  private duplicate search -> guard/exception disposition
  -> REINFORCED_EXISTING through update_payload
  OR -> semantic/exception fallthrough to CREATE

create:
  spawn_memory -> mark existing embed audit dirty (best effort)
  -> motif attach/create -> coherence/symbol/resonance
  -> symbol-state/payload enrichment (best effort) -> flush_node

postcommit:
  CREATED_NEW consumers: conflict -> SRG collision -> Hivemind
    -> motif maintenance -> derived
  every adapter context: world -> Character drift/gravity/reflex
    -> checkpoint -> compression -> proposal -> bridges
~~~

The create and reinforcement commit boundaries are deliberately asymmetric:

~~~text
CREATE_COMMIT = flush_node
CREATE_FLUSH_FAILURE = abort_unflushed_node -> structured canonical_commit_failed
REINFORCE_COMMIT = update_payload
REINFORCE_UPDATE_FAILURE = caught in duplicate attempt -> exception_fallthrough_to_create
~~~

Attach/create has no Fabric-level abort wrapper. Consequently its exact residue is failure-stage dependent:

- If the decision fails before mutation, the spawned entity, its precommit embedding/event/edge residue, and any successful audit dirty mark remain; caller receives the raised error.
- If attach/create mutates before its later save/event/split work fails, the in-memory motif can already reference the spawned EID and the registry may already have durable mutation. Fabric still raises and does not call abort.
- If attach/create succeeds and flush fails, abort_unflushed_node removes only the entity from live graph/physics/embedding lookup and live edges. It does not roll back MotifRegistry. The saved motif/member or new motif can therefore reference an EID that has no canonical nodes.jsonl record. Successful embed-audit dirty and symbol-state writes also remain.

~~~text
ORPHAN_MOTIF_FAILURE_RESIDUE =
  EXPLICIT_I4B_PARITY_OR_POLICY_GATE
~~~

I4B must characterize these stages separately. It must not silently add a transaction, rollback the motif, reuse the EID, or normalize an attachment error into canonical-flush failure.

### Bounded SRG same-entity write-path census

The census uses positive production call sites equivalent to MemoryGraph.update_payload, plus current native successor-materialization flows. A native recovery branch is part of its originating logical flow, not a third flow.

| ID | Call site / capability | Legacy or native | Exact predecessor / OCC | Query overlay applicability | Materialization / acknowledgement | Failure disposition | I4 owner |
|---|---|---|---|---|---|---|---|
| L01 | fabric.py:2189, retire prior identity anchor | Legacy | No revision witness; no OCC | Conditional on a live queried SRG entity; no legacy binding check | Legacy live-payload serialization only; no native acknowledgement | Local debug-suppressed best effort | I4D, with I4E SRG gate |
| L02 | fabric.py:2389, retire duplicate anchor | Legacy | No / no | Conditional | Legacy implicit / none | Local debug-suppressed best effort | I4D, with I4E SRG gate |
| L03 | fabric.py:2405, retire weak old anchor | Legacy | No / no | Conditional | Legacy implicit / none | Local debug-suppressed best effort | I4D, with I4E SRG gate |
| L04 | fabric.py:3783, ordinary private ingest reinforcement | Legacy | No / no | Yes for same live legacy entity | Legacy implicit / none | Duplicate-path catch falls through to CREATE | I4B-1 outcome contract and I4E SRG gate |
| L05 | fabric.py:5578, feedback reinforcement counter | Legacy | No / no | Conditional | Legacy implicit / none | No local catch at update site; feedback route owns visibility | I4G public-route classification and I4E SRG gate |
| L06 | fabric.py:5782, baton resolution lifecycle | Legacy | No / no | Conditional | Legacy implicit / none | Payload update is primary; later ledger failure is suppressed | I4G public lifecycle and I4E SRG gate |
| L07 | compression.py:833, short-path compression | Legacy | No / no | Conditional | Legacy implicit / none | Automatic caller suppresses; explicit operation has its own route disposition | Deep/compression policy gate |
| L08 | compression.py:866, long-path deep export mark | Legacy | No / no | Conditional | Legacy implicit / none | Deep export can precede failed core mark; automatic caller suppresses | Deep/compression policy gate |
| L09 | migration/apply.py:413, provenance migration apply | Legacy | No / no | Conditional if it operates in a live queried process | Legacy implicit / none | Catches update error and returns skipped anomaly; cursor is not appended | I4G maintenance classification and I4E SRG gate |
| L10 | spine.py:887, governance flag update | Legacy | No / no | Conditional | Legacy implicit / none | No local catch at update site; governance route owns visibility | I4G public-route classification and I4E SRG gate |
| N01 | fabric_native_routing.py:705/732, native private duplicate reinforcement (including recovery) | Native | Exact current revision and representation; OCC rechecked before source commit | Yes | Implemented prepare, exact revision validation, successor payload contribution, acknowledgement | Stale/unprovable materialization refuses before commit; acknowledgement is after source commit | I4E |
| N02 | native_derived_memory_runtime.py:510/531, native identity-anchor lifecycle successor | Native | Exact current revision and representation; typed successor OCC | Yes | Implemented prepare, exact revision validation, successor payload contribution, acknowledgement | Typed successor refuses before commit; any post-source acknowledgement error follows enclosing derived-slot disposition | I4D with I4E SRG gate |

~~~text
SRG_SAME_ENTITY_WRITE_PATH_COUNT = 12
SRG_SUCCESSOR_COVERED_PATH_COUNT = 2
SRG_SUCCESSOR_UNCOVERED_PATH_COUNT = 10
~~~

“Covered” means that a source-selected native flow already carries and acknowledges an exact-revision SRG materialization. It does not mean production activation is qualified. Every applicable uncovered path remains activation-blocking until it has an explicit I4 disposition; it must not receive a speculative materialization patch in I4AF.

### Legacy update_payload replacement fallback

The normal valid state has a mutable dictionary payload and a dictionary patch, so payload.update succeeds. If payload.update raises because a historical/corrupt/non-mutable payload is present, the fallback assigns the patch dictionary as the entire payload and then appends a canonical record. Thus the caller can report success while losing all other payload fields, including live SRG state, provenance, governance, and lifecycle data not present in the patch. If conversion of patch to a dictionary itself fails, the fallback also fails and no successful replacement occurs.

~~~text
SRG_update_payload_FALLBACK_DISPOSITION =
  HISTORICAL_CORRUPTION_COMPATIBILITY
~~~

The evidence establishes that it is not reachable through normal validated dictionary payload and patch inputs, but that it can be a successful destructive fallback for historical/corrupt runtime state. I4AFF freezes it as historical-corruption compatibility: native normal state must be mapping-shaped, or normalize a falsy legacy value before native work, and a truthy non-mapping root payload is a pre-activation normalization/disposition gate. A malformed patch remains a separately loud failure.

### Owner-level replay inventory

| Owner/effect | I4AF replay classification | Reason |
|---|---|---|
| Embed-audit dirty marking | BEST_EFFORT_WITH_RECONCILIATION | Dirty value is repeat-safe but timestamp changes; no key; repair/audit read observes it. |
| Motif attach/create and maintenance | NEW_PARITY_WITNESS_OR_REPLAY_KEY_REQUIRED | Precommit motif and postcommit maintenance can duplicate/mutate; residue must stay visible. |
| Conflict persistence | NEW_PARITY_WITNESS_OR_REPLAY_KEY_REQUIRED | Existing writer has no demonstrated owner key; later query observes absence/presence. |
| Derived memory / anchor lifecycle | NEW_PARITY_WITNESS_OR_REPLAY_KEY_REQUIRED | Existing native derived child keys are a staging fact, not generic legacy replay parity. |
| Proposal submission | NEW_PARITY_WITNESS_OR_REPLAY_KEY_REQUIRED | May have succeeded after primary commit before caller-visible failure. |
| Hivemind packet emission | NEW_PARITY_WITNESS_OR_REPLAY_KEY_REQUIRED | External packet/convergence effects may be partial. |
| Archive retrieval count | NEW_PARITY_WITNESS_OR_REPLAY_KEY_REQUIRED | Same operation replay must not become an unbounded extra count; distinct retrievals remain distinct. |
| Bridge suggestions | NOT_REPLAYABLE | Existing stochastic external effect intentionally propagates errors after primary commit. |
| Character drift state | SAFE_BY_CADENCE_STEP | Existing due-step cadence is the frozen replay posture; it does not create global exactly-once. |
| Character drift reflex | NOT_REPLAYABLE | Process-local rising-edge state resets; restart can re-fire an external callback. |
| Checkpoint | SAFE_BY_STEP_CADENCE | Periodic snapshot uses atomic replace; automatic failure is soft, not a global transaction. |
| SRG query overlay | PROCESS_LOCAL_NO_REPLAY | Restart absence matches legacy; only an exact-bound successor may materialize a current overlay. |

No classification above invents exactly-once semantics. A future replay key is a qualification prerequisite only when a future native route claims safe replay for that owner.

### Corrected qualification sequence

| Slice | Qualification target and rows | Actual dependency / blocker |
|---|---|---|
| I4B-1 | Primary outcome and pre-commit truth: input/provenance, memory create, reinforcement, embed-audit dirty marking, motif attach/create/order, precommit role/affect/symbol, residue, create/reinforce asymmetry | Requires stage-specific outcome and residue witnesses; mandatory Claude review after qualification. |
| I4B-2 | Post-commit motif tail: maintenance, split/merge where applicable, entropy, suggestions, identity anchors, fail-soft disposition | Depends on a qualified I4B-1 created outcome and motif live-order witness; separate verdict from I4B-1. |
| I4C | Conflict persistence and its existing query composition | Depends on created/private/core outcome facts; ConflictRegistry remains external. |
| I4D | Character seed, drift, gravity, reflex, and postcommit derived consumers | Depends on I4B outcomes and existing external Character/derived owners; gravity nested-write residue must be characterized. Precommit role/affect/symbol remains I4B-1. |
| I4E | SRG successor, collision feedback loop, world, trajectory, checkpoint | Blocked until this census receives mandatory Claude review; must preserve world -> Character -> checkpoint order and no SRG checkpoint capture. |
| I4F | Shared ingest, proposals, bridges, collective emission/convergence | Depends on scope/governance facts, not on an artificial archive/deep dependency. |
| I4G | Archive, index/promotion, reference, environment, baton, closure, feedback/governance/migration route classifications | Each remains a separate public/maintenance lifecycle owner; no ingest-tail conversion. |
| Deep/compression | Deferred | Requires a separate profile-policy decision. Enabled deep profile without parity remains activation-refused. |

~~~text
MANDATORY_CLAUDE_REVIEW =
  after I4B: outcome witness, precommit residue, motif order witness
  after this SRG same-entity census: before I4E successor implementation
  after I4E: SRG/world/checkpoint/restart composition
  before any deep/compression profile decision
~~~

### I4AF blockers

~~~text
I4B_BLOCKERS =
  stage-specific create/reinforce witness and orphan-motif policy/characterization
  + embed-audit, role/affect/symbol residue parity

I4C_BLOCKERS =
  external ConflictRegistry writer and per-operation replay witness

I4D_BLOCKERS =
  Character gravity nested-write characterization
  + drift/reflex restart replay disposition
  + retained external-owner composition

I4E_BLOCKERS =
  mandatory Claude census review
  + all applicable uncovered same-entity paths dispositioned
  + exact-revision refusal/acknowledgement verification

I4F_BLOCKERS =
  governance/scope, proposal/bridge propagation, and collective-owner parity

I4G_BLOCKERS =
  per-route classification and existing public-owner semantics

DEEP_PROFILE_POLICY_GATE =
  OPEN_PRE_ACTIVATION; enabled unsupported deep/compression profile refuses activation
~~~

## Activation blockers and retirement gates

~~~text
ACTIVATION BLOCKERS =
  all applicable I4 matrix-row tests and adversarial review not yet complete
  + native source-selected adapter/binder implementation not yet performed
  + SRG same-entity write-path census review and uncovered-path disposition incomplete
  + failure-disposition and replay parity unproven per external owner
  + enabled deep profile without native post-write parity
  + any owner migration, formula change, third scope, or live-order rewrite

RETIREMENT GATES =
  explicit per-matrix-row qualification
  + oracle/characterization tests for order, owner, outcome, and failure behavior
  + Claude adversarial approval of the relevant slice
  + authorized production activation decision
  + separate retirement authorization
~~~

Even a passing later slice is not retirement authorization. There is no proposal in I4A to delete an old writer, registry, adapter, public route, or external durable store.

## Initial I4A conclusion — superseded by I4AFF final verdicts

~~~text
POST_WRITE_CALL_GRAPH_MAPPED = YES
POST_WRITE_FAILURE_BOUNDARIES_MAPPED = YES
EXTERNAL_DURABLE_OWNERS_MAPPED = YES
POST_WRITE_FORMULA_CHANGES_REQUIRED = NO
ONE_POST_WRITE_SEMANTIC_IMPLEMENTATION_FEASIBLE =
  YES_WITH_SOURCE_SELECTED_ADAPTERS_AND_EXTERNAL_OWNER_BINDERS
I4_IMPLEMENTATION_READY =
  SUPERSEDED_BY_I4AFF_FINAL_VERDICTS
~~~

This result is feasible because the current post-write seam already separates a primary storage adapter, a context/outcome object, memory access, and dependency adapters. It is not evidence that a single native writer can own all durable state or that all external effects are transactionally replayable.

## I4AFF final architecture freeze

### Cross-route SRG process-state capabilities

The denominator now includes two independent process-local Fabric capabilities. They satisfy the matrix cross-route rule because ingest writes each value and a different live route consumes it to alter observable or cognitive behavior.

| Capability | Write | Read and semantic effect | Owner / restart |
|---|---|---|---|
| C75 — SRG last-ingest-band coupling | SRG-enabled ingest stores current R_band under (workspace_id, agent_id). | Query and trace compare a hit band to that agent's stored band and apply the existing 1.08 same-band multiplier on equality. | Process-local Fabric map; cleared at restart, so no bonus can fire until later ingest. |
| C76 — SRG relational EMA | SRG-enabled ingest seeds relational L_amplitude on first observation; later writes use 0.8 previous plus 0.2 new. | Fabric getter feeds Spine, which supplies the value to harvest_geometric_context as srg_relational; ingest history therefore affects later advisory geometric context. | Process-local Fabric map; cleared at restart. |

~~~text
CROSS_ROUTE_PROCESS_STATE_RULE =
  process-local Fabric state written on one live route and read on another,
  when it changes observable or cognitive behavior, is a functional capability
  with its own matrix disposition; it is not merely a cache.

SOURCE_DOCSTRING_CORRECTION =
  the historical claim that SRG relational EMA has no wired consumer is stale;
  Spine is the verified consumer. This memo is the documentation correction;
  no production source file is changed in I4AFF.
~~~

### Reinforcement routes are distinct

| Route | Selection and outcome | Post-write relationship |
|---|---|---|
| Ingest duplicate reinforcement | Duplicate-search based; private-only; cross-class and canon-contradiction guards can select CREATE; duplicate-path errors can fall through to CREATE; produces normal storage outcome. | Reaches the always-run LegacyFabricPostWriteAdapter tail, while CREATED_NEW consumers remain create-only. |
| Explicit Fabric.reinforce / Spine reinforce | Targets named EIDs; no duplicate search or CREATE fallthrough; uses its own route guards and has no storage-outcome witness today. | Does not run LegacyFabricPostWriteAdapter. |

Both are same-entity legacy update_payload writes and can carry live SRG state. They must never be collapsed into one outcome architecture.

### Frozen precommit residue and nested Character-write policy

~~~text
ORPHAN_MOTIF_POLICY =
  PRESERVE_DURABLE_PRECOMMIT_MOTIF_RESIDUE

FAILED_MEMORY_BECOMES_CANONICAL = NO
FAILED_EID_MAY_BE_REUSED = NO
DURABLE_PRECOMMIT_MOTIF_MUTATION = PRESERVED
FAKE_CANONICAL_MEMORY = PROHIBITED
RESTART_STABLE_DURABLE_EVIDENCE = REQUIRED
~~~

After successful motif save followed by canonical flush failure, legacy abort removes the entity from live graph state but leaves the consumed EID and durable motif membership/state. Its member count, density, gravity bonus, domain-centroid weighting, and active-motif ordering remain cognitively observable. Native must preserve equivalent motif cognition, not roll it back merely because its storage can transact.

When attach/create itself fails, I4B qualifies only state that actually committed before the exact injected failure point. It must not manufacture a generic orphan solely because attach/create raised. The preferred representation is an existing lifecycle, provenance, or failed-intent primitive if it can represent the fact honestly. If no existing substrate primitive can retain the needed durable evidence without making a failed memory canonical/queryable or allowing EID reuse, I4B stops and returns to GPT before schema invention.

Character gravity is a bounded internal nested write: spawn, motif attach, flush. It does not call Fabric.ingest and does not re-enter the post-write adapter.

~~~text
CHARACTER_GRAVITY_NESTED_CANONICAL_WRITE = YES
POST_WRITE_RECURSION = NO
ORPHAN_MOTIF_POLICY_APPLIES_TO_GRAVITY = YES
~~~

### Frozen update_payload compatibility boundary

~~~text
UPDATE_PAYLOAD_FALLBACK_CLASSIFICATION =
  HISTORICAL_CORRUPTION_COMPATIBILITY

QUALIFIED_NORMAL_PAYLOAD =
  mapping
  OR falsy legacy value normalized to empty mapping before native operation

PREACTIVATION_ROOT_GATE =
  no entity payload is a truthy non-mapping value

TRUTHY_NONMAPPING =
  normalize or disposition before activation

PATCH_NOT_DICT_CONVERTIBLE =
  legacy update_payload raises
  native parity fails loud
~~~

Native normal behavior must not reproduce the silent full-payload replacement fallback. The historical compatibility case and malformed-patch case are distinct.

### SRG policy, coverage law, and physical path census

~~~text
SRG_QUERY_BREATHING_STORAGE = PROCESS_LOCAL
SRG_QUERY_BREATHING_CONSEQUENCE = MAY_AFFECT_POST_WRITE_COLLISION

NO_OVERLAY = normal write
OVERLAY_LOST_BY_RESTART = absent
CURRENT_OVERLAY_PLUS_SAME_ENTITY_SUCCESSOR = materialize canonical successor payload
STALE_PREDECESSOR = refuse precommit
UNPROVABLE_OVERLAY_READ = refuse precommit with distinct reason

QUERY_TAIL_BREATHING_WRITEBACK_FAILURE = FAIL_SOFT
SAME_ENTITY_SUCCESSOR_MATERIALIZATION_FAILURE = FAIL_CLOSED_PRECOMMIT

EXACT_BINDING =
  core + source/scope namespace + EID + predecessor revision
~~~

The query-to-ingest loop remains named parity: query breathing creates a process overlay; a later CREATED_NEW ingest collision scan reads effective SRG state; collision can change existing and incoming SRG state; later queries then change.

~~~text
SRG_SAME_ENTITY_WRITE_PATH_COUNT = 12
SRG_SUCCESSOR_COVERED_PATH_COUNT = 2
SRG_SUCCESSOR_UNCOVERED_PATH_COUNT = 10
PHYSICAL_PATH_COUNT != LIVE_SEMANTIC_GAP_COUNT

SRG_SUCCESSOR_COVERAGE_LAW =
  every applicable live same-entity write path must use qualified successor
  materialization or be structurally refused under native authority until parity exists.
~~~

| Path class | Frozen disposition |
|---|---|
| Live: anchor supersession, motif/anchor pruning, weak-member demotion, ingest duplicate reinforcement, explicit Fabric/Spine reinforce, baton consumption, governance full-payload update | Requires I4E successor parity or structural native refusal. |
| Profile-conditional: compression short and long | Governed by the deferred deep/compression profile policy; do not wire first. |
| Historical: migration apply | Historical/migration-only; do not retrofit native predecessor protocol solely to equalize counts. |
| Existing native covered flows | Qualified native reinforcement and native typed identity-anchor lifecycle successors only; no claim that remaining legacy paths have native equivalents. |

### Owner-level replay freeze

| Effect | Frozen classification |
|---|---|
| Conflict persistence, derived memory, proposal submission, Hivemind emission, archive retrieval count, motif mutation | REPLAY_WITNESS_REQUIRED |
| Bridge suggestions | NOT_REPLAYABLE |
| Character drift | SAFE_BY_CADENCE_STEP where its existing cadence contract applies |
| Character reflex | NOT_REPLAYABLE_SAFELY; process-local rising edge and undeclared external callback can re-fire after restart |
| Checkpoint | SAFE_BY_CADENCE_STEP |
| Embed audit | Reasserts dirty=true; health observability consumer only, not a cognitive consumer |

~~~text
GLOBAL_EXACTLY_ONCE_REQUIRED = NO
NO_INVENTED_GLOBAL_EXACTLY_ONCE = YES
DEEP_COMPRESSION_PROFILE_POLICY = OPEN
~~~

### Frozen sequence and reviews

~~~text
I4B = B-1 primary outcome/precommit truth; B-2 postcommit motif tail
I4C = conflict persistence
I4D = Character plus postcommit derived effects
I4E = SRG plus world, trajectory, checkpoint
I4F = shared ingest, proposals, bridges, collective emission
I4G = archive, reference, environment, baton, closure public lifecycle
DEEP_COMPRESSION = deferred pending profile policy

I4G_BATON_CROSS_SLICE_INVARIANT =
  baton lifecycle owns an I4E SRG same-entity successor obligation

R1 = after I4B before I4C
R2 = census reviewed/frozen; reopen only for denominator change or material expansion
R3 = after I4E before I4F
R4 = before deep/compression profile policy
~~~

### Final I4A verdicts

~~~text
P9D_I4A_POST_WRITE_DEPENDENCY_ARCHITECTURE = FROZEN
FUNCTIONALITY_PRESERVATION_MATRIX = QUALIFIED_BASELINE
FUNCTIONALITY_DENOMINATOR_COUNT = 76
MAPPED_CAPABILITY_COUNT = 76
UNMAPPED_CAPABILITY_COUNT = 0

PRIMARY_OUTCOME_MODEL = FROZEN
PRECOMMIT_RESIDUE_MODEL = FROZEN
ORPHAN_MOTIF_POLICY = PRESERVE_DURABLE_PRECOMMIT_MOTIF_RESIDUE
SRG_POLICY = FROZEN
SRG_WRITE_PATH_CENSUS = FROZEN_12_PATH_DENOMINATOR
SRG_SUCCESSOR_COVERAGE_POLICY = FROZEN
UPDATE_PAYLOAD_HISTORICAL_CORRUPTION_POLICY = FROZEN
REPLAY_POLICY = OWNER_LEVEL_NO_GLOBAL_EXACTLY_ONCE
I4_IMPLEMENTATION_SEQUENCE = FROZEN

POST_WRITE_FORMULA_CHANGES_REQUIRED = NO
ONE_POST_WRITE_SEMANTIC_IMPLEMENTATION_FEASIBLE = YES
I4B_IMPLEMENTATION_READY = YES
RETIREMENT_ALLOWED = NO
REAL_PRODUCTION_ACTIVATION = NOT_AUTHORIZED
~~~
