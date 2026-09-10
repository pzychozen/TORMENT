# TORMENT Database Convergence — Real-Root Disposition Owner Operation Contract v1.2

**Status:** **RATIFIED — DESIGN CONTRACT ONLY.** This supersedes the canonical
v1.1 contract. It ratifies the previously absent world-trajectory handoff
owner and protocol; it does **not** create that owner, run a handoff, mutate a
real root, alter the selector, or execute P7.

**Date:** 2026-09-10
**Authoritative starting commit:** `0169897add00f2a36203fc347cf7ca88a15b7f51`
**Corrected core:** `f21c730f-5222-4aa8-9a5f-1c1188456df3`
**P6 receipt:** `f5efc57f-28a0-4ce2-bfc4-2787c15bafb1`

## Ratification verdict

```text
REAL_ROOT_MUTATION                         = NONE
REAL_ROOT_UNCHANGED                        = YES
REAL_P7_EXECUTED                           = NO
SELECTOR_MUTATION                          = NONE
SELECTOR_GENERATION                        = 7
SELECTOR_STATE                             = CUTOVER_PENDING
PUBLIC_API                                 = MAINTENANCE_ONLY

TRAJECTORY_HANDOFF_OWNER_RATIFIED          = YES
WRITER_EXCLUSIVITY_KEY_DEFINED             = YES
LEGACY_QUIESCENCE_DEFINED                  = YES
NATIVE_ADMISSION_DEFINED                   = YES
WRITE_TIME_FENCING_DEFINED                 = YES
IDEMPOTENCE_DEFINED                        = YES
PARTIAL_FAILURE_DEFINED                    = YES
RESTART_RECOVERY_DEFINED                   = YES
HANDOFF_RECEIPT_DEFINED                    = YES
P7_PRECONDITION_RATIFIED                   = YES
DUAL_WRITE_POSSIBLE                        = NO
NEW_HIDDEN_AUTHORITY                       = NO

TRAJECTORY_HANDOFF_CONTRACT                = RATIFIED
ROOT_DISPOSITION_OWNER_CONTRACT            = RATIFIED
```

The new authority is deliberately narrow: it coordinates the transfer of the
right to write trajectory artifacts. It neither understands trajectory
semantics nor owns the source world, SQLite memory, Character, motifs,
proposals, selector activation, or process control.

## Complete disposition classification

The ten non-trajectory determinations from v1.1 are carried forward exactly;
their owners, frozen predecessors/successors, and receipt laws are unchanged.
The sole change is that `world_trajectory` is now a ratified real authority
transition instead of an owner-absent placeholder.

| Frozen disposition ID | Classification | Ratified owner / completion boundary | P7 waits? |
| --- | --- | --- | --- |
| `bridge_registry` | `REAL_RECEIPT_ONLY` | `BridgeRegistry` conservation receipt | YES |
| `character_active_baseline` | `REAL_MUTATION_REQUIRED` | future narrow `CharacterStore` target-geometry rebaseline | YES |
| `character_drift_history` | `REAL_RECEIPT_ONLY` | `CharacterStore` conservation receipt | YES |
| `character_seed` | `REAL_RECEIPT_ONLY` | `CharacterStore` seed conservation receipt | YES |
| `checkpoint_kernel_calibration` | `SYNTHETIC_ONLY_NO_PRODUCTION_ANALOG` | prior live-context/checkpoint evidence | NO |
| `conflict_role_affect_identity` | `REAL_RECEIPT_ONLY` | existing conflict/role/affect/identity owners | YES |
| `deep_archive_vector_state` | `REAL_RECEIPT_ONLY` | retained disabled deep owner | YES |
| `hivemind_historical_geometry_scores` | `REAL_RECEIPT_ONLY` | `CollectiveField` / proposal-bridge conservation receipt | YES |
| `proposal_registry` | `REAL_RECEIPT_ONLY` | `ProposalRegistry` plus public dispatch-refusal receipt | YES |
| `srg_payload_markers` | `SYNTHETIC_ONLY_NO_PRODUCTION_ANALOG` | admitted core payload evidence | NO |
| `world_trajectory` | `REAL_AUTHORITY_TRANSITION_REQUIRED` | future `TrajectoryWriterHandoffCoordinator` per-scope handoff receipt | YES |

```text
REAL_MUTATION_REQUIRED_COUNT                 = 1
REAL_AUTHORITY_TRANSITION_REQUIRED_COUNT     = 1
REAL_RECEIPT_ONLY_COUNT                      = 7
SYNTHETIC_ONLY_NO_PRODUCTION_ANALOG_COUNT    = 2
OWNER_ABSENT_COUNT                           = 0
CLASSIFICATION_TOTAL                         = 11
ALL_11_DISPOSITIONS_CLASSIFIED               = YES
ALL_REQUIRED_REAL_OWNERS_DEFINED             = YES
```

## Production trajectory-writer archaeology

Counts below are code-path classes, not an assertion about currently live
process instances. Static source review cannot legitimately invent a live
process count.

### Legacy writer paths

| Writer / creation path | Process and scope boundary | Artifact target and lifecycle | Registration, liveness, maintenance/restart |
| --- | --- | --- | --- |
| `MemoryGraph.traj` in `torment_service/memory_graph.py`; it selects `TrajectoryV2Writer` by default or `TrajectoryLogger` for explicit legacy format. | Any Fabric-hosting Python process. One graph root is either private `workspaces/<ws>/agents/<agent>/private` or shared `workspaces/<ws>/domains/<domain>/shared`. | V2 writes `trajectories/v2/{entity_genesis.jsonl,boundaries.jsonl,manifest.jsonl,diagnostics.jsonl,chunks/**}`; legacy writes `logs/trajectories/daily/*.jsonl` (or its compatibility `trajectories.jsonl`). Construction creates the writer; `spawn_memory`, reset, and `step_world` write; V2 `close` seals a tail. | No writer registration or scope lease exists. The P2 `RootWriterFreezeEvidence` / injected Windows census can observe broad process classes but not a scope-bound live writer. A direct `MemoryGraph` can be constructed after public maintenance and after restart, so existing code can recreate authority. |
| `Workspace.__init__` and `Workspace.add_domain` in `torment_service/fabric.py`. | Legacy Fabric process; shared `RootScopeKey(workspace, SHARED, domain)`. | Creates one `MemoryGraph` per shared domain during workspace construction or domain addition. It becomes able to write immediately; normal graph closure closes only its V2 tail. | No registration. Maintenance-only public runtime does not prevent a direct Fabric/Workspace process from constructing this graph. Restart repeats construction. |
| `TormentFabric.create_agent` in `fabric.py`. | Legacy Fabric process; private `RootScopeKey(workspace, PRIVATE, agent)`. | Creates and retains the private `MemoryGraph`; its normal memory/post-write work can reach `spawn_memory` and `step_world`. | No registration or cross-process liveness. A restarted Fabric re-creates the private graph. |
| `_baton_private_graph_view` and `_closure_workspace_graph_views` in `fabric.py`. | Legacy Fabric process; existing private root. | Construct transient `MemoryGraph` views for persisted private scopes. Even where current callers use them for inspection, construction creates a trajectory writer capable of later writes. | No registration. A cold process can construct these views after maintenance is enabled; restart repeats it. |

`TrajectoryLogger` and `TrajectoryV2Writer` are sinks, not handoff owners.
Their current constructors and write methods perform filesystem work directly;
they do not inspect selector state, P6 evidence, a writer generation, or a
cross-process lease.

### Native writer paths

| Writer / creation path | Process and scope boundary | Artifact target and lifecycle | Registration, liveness, maintenance/restart |
| --- | --- | --- | --- |
| `NativeTrajectoryEvidenceRuntime` in `torment_service/substrate/native_trajectory_evidence_runtime.py`, reached by private I4E post-write. | One `NativeProductionResourceOwner` process; key is currently only `(core_id, legacy_source_namespace_id)`. The source is a private admitted scope. | Delegates to the same V2/legacy artifact roots as `MemoryGraph`; writes genesis, frames, and classification events. `NativePrivateTrajectoryEvidenceProcessState` retains it until production-owner close, which seals V2 tails. | The state is an in-process `dict` guarded by `threading.RLock`; no durable registration or cross-process liveness exists. A service restart reconstructs it. |
| The shared D3/E1 route in `NativeFabricPostWriteAdapter._shared_trajectory_runtime`. | Request-scoped native adapter for an admitted shared domain. | Creates `NativeTrajectoryEvidenceRuntime` for `workspaces/<ws>/domains/<domain>/shared`; it is closed when its post-write context closes. | No registration and no process-wide ownership. Two process/request contexts can each create a writer. Restart recreates it. |

`NativeWorldRuntime` supplies the process-local source entities but is not an
artifact writer. `NativeProductionWriteContext.route` and
`NativeProductionPostWriteContext.run` revalidate the deployment agreement,
which protects native core routing only; neither supplies a trajectory writer
fence at the eventual filesystem write.

```text
LEGACY_TRAJECTORY_WRITER_COUNT / CLASSES = 1 writer family (`MemoryGraph`) / 4
                                            production construction paths / 2 sink formats
NATIVE_TRAJECTORY_WRITER_COUNT / CLASSES = 1 writer family
                                            (`NativeTrajectoryEvidenceRuntime`) / 2
                                            lifecycle bindings / 2 sink formats
CURRENT_WRITER_REGISTRATION               = NONE
CURRENT_CROSS_PROCESS_WRITER_FENCE         = NONE
CURRENT_CROSS_PROCESS_LIVENESS             = NONE
```

## Existing evidence and the genuine gap

P2 root writer-freeze evidence is valuable input. It requires all five broad
writer observations to be `STOPPED` or `ABSENT`, an absent listener, terminal
clone/repair jobs, and stable workspace-tree snapshots. The Windows census
also refuses unresolved/running direct tool or script processes. It is,
however, expressly an injected observation and not process control or a
durable writer lease. It has no per-scope writer identity and does not make a
subsequent direct file append fail.

`NativePrivateTrajectoryEvidenceProcessState` is likewise useful only inside
one Python process. It cannot find legacy writers in another process and
cannot prevent a second process from creating the same writer.

Therefore no existing component can satisfy the required cross-process
invariant. A new component is necessary, but only for trajectory ownership
coordination.

## Ratified owner, scope, and exclusivity

```text
TRAJECTORY_HANDOFF_OWNER_NAME      = TrajectoryWriterHandoffCoordinator
TRAJECTORY_HANDOFF_OWNER_AUTHORITY = create and verify durable, per-scope
                                     trajectory-writer authority records;
                                     fence an old registered writer generation;
                                     admit/rotate one native writer session;
                                     issue immutable handoff receipts
TRAJECTORY_HANDOFF_OWNER_STORAGE   = <data-root>/substrate/trajectory_writer_handoff/
                                     authority.sqlite plus one coordinator-owned
                                     scope lock namespace
TRAJECTORY_HANDOFF_OWNER_SCOPE     = only the materialized private/shared
                                     RootScopeKey universe bound by the active
                                     P6 root-completion admission description
SELECTOR_MUTATION_CAPABILITY        = NO
GENERAL_PROCESS_CONTROL_CAPABILITY  = NO
ARBITRARY_STORAGE_MUTATION_CAPABILITY = NO
```

The future sidecar must be its own strictly typed SQLite schema, opened with
the same durable SQLite discipline used by selector storage (`FULL`
synchronous mode and WAL) but not sharing selector tables or selector
operations. It may record only coordinator state, registrations, fenced
generations, write intents, and receipts. It cannot change deployment mode or
admit a native memory core.

The exact unit of exclusivity is one physical admitted trajectory artifact
root, not a process, a format, or an entity:

```text
WRITER_EXCLUSIVITY_KEY = SHA-256(
  data_root_identity,
  RootScopeKey.identity_payload(),
  legacy_source_namespace_id,
  canonical_artifact_root_identity
)
```

`RootScopeKey` supplies exactly one of `(workspace, PRIVATE, agent)` or
`(workspace, SHARED, domain)`. The source namespace and canonical root prevent
an accidental alias from collapsing separate admitted scopes; the trajectory
format is a binding property, not part of the key, so V2 and legacy-format
writers can never coexist at one root.

The expected scope universe is the exact P6 root-completion census of
**materialized** `RootScopeKey` values. Declared-empty shared scopes have no
physical source root and are excluded only by their typed
`DECLARED_EMPTY_SHARED` posture. No path discovery may add a scope. A future
handoff invocation refuses if its typed scope census differs from that P6
universe or if two records resolve to one artifact root.

```text
AUTHORITATIVE_TRAJECTORY_WRITER_COUNT_PER_SCOPE <= 1
POST_HANDOFF_AUTHORITATIVE_NATIVE_WRITER_COUNT  = 1
POST_HANDOFF_AUTHORITATIVE_LEGACY_WRITER_COUNT  = 0
```

Historical files and dormant Python objects are not writers. A writer is
authoritative only when it owns the current coordinator generation and an
active guarded writer session for this key.

## Durable predecessor and quiescence law

For each scope, the handoff may begin only when all of the following are
mechanically inspectable and exactly bound:

```text
P6 core is ACTIVE_CORE / NATIVE_ACTIVE and has corrected-core binding
selector is generation 7 / CUTOVER_PENDING and public runtime resolves MAINTENANCE_ONLY
the P6 root-completion witness, Envelope D, plan digest, and frozen
  `world_trajectory = RETAIN` disposition are valid
the scope belongs to the exact materialized P6 census and maps to one canonical root
the coordinator record is LEGACY_AUTHORITATIVE with one known legacy generation
  or is freshly initialized from a valid no-live-writer P2 freeze epoch
native writer is absent/non-authoritative
no matching completed receipt exists
all prior write-intent ledger rows are settled and a fresh per-root artifact
  observation is readable
```

Any mismatch is `WRONG_PREDECESSOR -> REFUSE`.

`LEGACY_QUIESCED` has a stronger meaning than ceasing to create objects. The
future implementation must require all of these before it commits the legacy
fence:

1. The fresh P2-class writer-freeze recheck and injected census show every
   broad writer class stopped or absent; unresolved evidence refuses.
2. Every registered legacy writer client for the exact scope has entered
   `QUIESCING`, stopped new genesis/frame/classification writes, sealed any V2
   tail it owns, and recorded a close acknowledgement.
3. The scope write-intent ledger has no in-flight or ambiguous entry, and a
   fresh artifact-root stability observation matches the quiescence evidence.
4. The coordinator holds the same scope lock used by all future actual writes
   while it increments the durable authority generation and revokes legacy.

The first rollout must deploy the guarded legacy writer client before a real
handoff. An older, unguarded process is not grandfathered: it cannot satisfy
registration coverage, and the P2 census must show it absent before the
operation proceeds. The coordinator does not terminate that process; it fails
closed until the existing maintenance procedure establishes its absence.

```text
LEGACY_QUIESCENCE_MECHANISM      = fresh P2 freeze/census + registered-client
                                  close acknowledgements + settled write ledger
                                  + scope-lock-protected durable generation fence
LEGACY_WRITER_REENTRY_AFTER_HANDOFF = REFUSED
```

## Write-time fence and cross-process critical section

A future `TrajectoryWriterAuthorityClient` is required at every production
trajectory write boundary: V2 constructor epoch/boundary work, genesis, reset
boundary, frame/tail finalization, legacy JSONL append, and native
classification-event append. Raw sink construction must not remain a
production authority path.

The authority client receives a scope key, writer family, stable writer-slot
identity, and opaque current generation/session token. For every artifact
effect it must:

1. acquire the coordinator's OS-backed exclusive scope lock;
2. read the durable record under a write transaction and prove that its family,
   slot, generation, and session equal the current record and that the phase
   permits that effect;
3. durably record a bounded write intent, then write/fsync the artifact while
   retaining the same scope lock;
4. durably settle the intent with the resulting artifact identity/digest before
   releasing the lock.

The fence transition uses this same lock. It cannot commit until all intent
rows are settled, and a writer that wakes after the fence has lost its token
and fails before the file append. A crash between intent and settlement blocks
handoff; recovery reconciles the exact declared effect against the artifact.
If that reconciliation is not exact, it refuses and requires manual review.

```text
WRITE_AUTHORITY_CHECK = scope lock + durable current-generation/session
                        comparison immediately before each artifact effect
TRAJECTORY_WRITE_WITH_STALE_AUTHORITY -> REFUSE
WRITE_PATH_IMPLEMENTATION_CHANGE_REQUIRED = YES
```

This makes coordination cross-process. It does not rely on a Python dict,
notification, timeout, or a process voluntarily receiving an in-memory
message. A stale process that never sees a notification still fails at the
next guarded write. A stale unguarded deployment prevents the handoff from
starting rather than becoming an exception to the fence.

## Durable handoff state machine

The sidecar stores a per-scope phase, monotonic authority generation, current
writer family/slot/session, legacy-fence generation, immutable transition
evidence digests, and terminal receipt reference. A writer session can rotate
only by incrementing the same native generation under the scope lock; this is
native-only recovery, not a fresh handoff and never restores legacy authority.

| Durable phase | Legal artifact writer | Legal next action and durable evidence | Restart interpretation | P7 |
| --- | --- | --- | --- | --- |
| `LEGACY_AUTHORITATIVE` | Exactly the registered legacy generation/session. | `begin_quiesce`; record scope/P6/predecessor digest and prohibit new legacy sessions. | Resume as legacy only; no native admission. | Forbidden |
| `QUIESCING` | No new legacy payload writes; an already registered legacy client may take the guard solely to close/seal and acknowledge. | `fence_legacy` only after the full quiescence proof and empty ledger. | Re-read registrations/ledger; resume quiescence or stop for ambiguous intent. | Forbidden |
| `LEGACY_QUIESCED` | None. | The transition to this phase atomically records the incremented legacy-fence generation. `begin_native_admission` binds exact native facts. | No legacy re-entry is possible; resume native-admission preparation only. | Forbidden |
| `NATIVE_ADMITTING` | None. | `admit_native_writer` records exactly one native slot/session after rechecking P6/core/scope/fence bindings. | Resume this stage; a missing or mismatched native slot refuses. | Forbidden |
| `NATIVE_AUTHORITATIVE` | Exactly the admitted native session under its current generation. | Verify one current native session and append the immutable per-scope receipt. | A replacement native session must fence the old native session before it can write; no legacy route is available. | Forbidden |
| `HANDOFF_COMPLETE` | Exactly one current native session for the recorded native slot. | Native-only session recovery may fence/replace a stale native session while preserving the terminal transfer receipt. | Receipt persists; P7 remains ineligible until a current native session is freshly verified after recovery. | Eligible only with all aggregate gates |

The only forward handoff path is:

```text
LEGACY_AUTHORITATIVE
  -> QUIESCING
  -> LEGACY_QUIESCED       (quiescence proof and legacy fence committed)
  -> NATIVE_ADMITTING
  -> NATIVE_AUTHORITATIVE  (one native slot/session admitted)
  -> HANDOFF_COMPLETE      (verification and receipt committed)
```

No transition returns to legacy. `NATIVE_ADMITTING` permits no native artifact
write. Thus native admission cannot overlap a legacy-authoritative writer.

## Native admission and idempotence

The future admission operation may be called only by a native runtime that
presents typed `NativeProductionAuthorityFacts`, including the corrected core
ID, P6 receipt/core witness, active scope's
`legacy_source_namespace_id`, `RootScopeKey`, canonical artifact root, and
the coordinator's preceding legacy-fence generation. The coordinator allocates
one durable native writer-slot ID and one current session generation. The
process instance ID is evidence only; it cannot self-declare a writer slot.

```text
NATIVE_ADMISSION_MECHANISM = coordinator `admit_native_writer` transaction
                             under the scope lock, bound to exact active-core,
                             P6, scope, fence, and writer-slot facts
```

| Observed request/state | Required result |
| --- | --- |
| Fresh exact predecessor | Perform only the next legal transition. |
| Exact terminal request and matching receipt | Return the existing receipt; no duplicate transition. |
| Mid-protocol durable phase with exact operation binding | Resume only from that phase after its required rechecks. |
| Different operation key, scope binding, legacy predecessor, P6/core fact, or native writer slot | `REFUSE`. |
| Old legacy writer attempts registration or write after `QUIESCING`/fence | `REFUSE`. |
| Second native writer session without a coordinator-authorized native-only rotation | `REFUSE`. |
| Ambiguous write intent/artifact reconciliation | `STOP_FOR_MANUAL_REVIEW`; P7 remains forbidden. |

No automatic time-based lease expiry is authorized. A process/service/machine
restart uses a lock-protected native-session replacement: it increments the
native session generation before the replacement can write, so an old process
can resume only to a stale-token refusal. This preserves one writer even if
the old process was merely paused rather than known dead.

## Partial failure and recovery law

There is no rollback to P5, no selector change, and no attempt to reinstate
legacy authority after P6. All recovery starts by reading the sidecar and
revalidating P6/root bindings.

| Failure boundary | Durable state / legal writer | Safe recovery | P7 |
| --- | --- | --- | --- |
| Before quiescence | `LEGACY_AUTHORITATIVE`; exact registered legacy only. | Retry `begin_quiesce` with same operation key or refuse conflicting intent. | Forbidden |
| During quiescence | `QUIESCING`; only guarded seal/ack work. | Recheck every registration, ledger, freeze evidence, and artifact stability; resume or manual review. | Forbidden |
| After quiescence, before fence | `QUIESCING`; legacy has not been revoked. | Settle/reconcile intent and repeat all quiescence checks before fencing. | Forbidden |
| After fence, before native admission | `LEGACY_QUIESCED` or `NATIVE_ADMITTING`; no artifact writer. | Revalidate exact native binding and continue only native admission. | Forbidden |
| During native admission | `NATIVE_ADMITTING`; no artifact writer until the admission commit. | Match the durable writer slot or refuse; then admit one session. | Forbidden |
| After native admission, before verification | `NATIVE_AUTHORITATIVE`; one guarded native session only. | Verify/fence-replace the native session if required, then continue. | Forbidden |
| After verification, before receipt | `NATIVE_AUTHORITATIVE` plus durable verification evidence; one native session only. | Recheck the evidence and append exactly one matching receipt. | Forbidden |
| After receipt, process/service/machine restart | `HANDOFF_COMPLETE`; old session is not implicitly live. | Recover/re-fence one native session and rerun current-session verification. The historical receipt remains immutable. | Forbidden until current verification and aggregate check pass |

The coordinator crash changes no authority by itself because the last durable
phase, fence, and write-intent rows are decisive. Process death releases an OS
lock but not a generation: the replacement must fence/revalidate before it can
write. Machine restart likewise has no implicit legacy restoration.

## Per-scope and aggregate receipts

A successful per-scope receipt is immutable and binds at least:

```text
contract/version and `world_trajectory` frozen disposition
data-root identity and WRITER_EXCLUSIVITY_KEY payload/digest
RootScopeKey, legacy_source_namespace_id, canonical artifact-root identity
legacy predecessor writer family/slot/generation and quiescence evidence digest
fresh P2 freeze/census evidence digest, settled-ledger digest, and artifact observation digest
legacy fence generation
native writer-slot identity, session generation, native admission evidence
corrected core ID, P6 receipt, root-completion/Envelope-D witness, plan digest
operation/retry identity, terminal HANDOFF_COMPLETE phase, and receipt digest
```

It proves the ordering of actual authority records; a free-text “handoff
successful” statement is not a receipt.

The root trajectory disposition is closed only by a non-mutating aggregate
verifier receipt that binds the P6 materialized-scope census and every
per-scope receipt. It must report:

```text
EXPECTED_SCOPE_COUNT             = exact cardinality of the bound materialized P6 scope census
COMPLETED_SCOPE_COUNT            = EXPECTED_SCOPE_COUNT
UNACCOUNTED_SCOPE_COUNT          = 0
OVERLAPPING_OWNER_SCOPE_COUNT    = 0
EVERY_SCOPE_CURRENT_NATIVE_COUNT = 1
EVERY_SCOPE_CURRENT_LEGACY_COUNT = 0
TRAJECTORY_DISPOSITION_COMPLETE  = TRUE
```

Duplicate keys, duplicate artifact roots, a missing receipt, a stale current
native session, or a receipt whose P6/core/plan binding disagrees with the
aggregate are refusal conditions.

## P7, Character, and preserved negative authority

P7 is a future selector operation and remains unexecuted here. Its ratified
precondition is:

```text
all trajectory handoff scope receipts and the aggregate trajectory receipt validate
+ the one Character target-geometry rebaseline receipt validates
+ all seven receipt-only conservation/guard receipts validate
+ both synthetic-only dispositions bind to their prior qualified evidence
+ the aggregate root disposition receipt validates against the same P6/root facts
```

The two synthetic-only records do not require a production operation.

```text
TRAJECTORY_CHARACTER_ORDER_DEPENDENCY = NO
```

Trajectory authority controls artifact writers; Character baseline controls
two fields in `CharacterState`. Neither operation is a predecessor or
successor of the other. Both remain independently required before P7.

```text
35_MEMORY_CERTIFIED_REFUSALS                = PRESERVED
23_MOTIF_CERTIFIED_REFUSALS                  = PRESERVED
76_PRIVATE_PLANS_MOTIF_DOMAIN_NONE           = PRESERVED
MODEL_D_CHANGED                              = NO
CERTIFIED_REFUSAL_SEMANTICS_CHANGED          = NO
SELECTOR_MUTATION_CAPABILITY                 = NO
CHARACTER_SEMANTICS_CHANGED                  = NO
PROPOSAL_SEMANTICS_CHANGED                   = NO
COLLECTIVE_HIVEMIND_SEMANTICS_CHANGED        = NO
DUAL_READ_AUTHORITY_POSSIBLE                 = NO production grant
AUTOMATIC_POST_P6_ROLLBACK                   = NO
```

## Future implementation impact map

This is an implementation order, not authorization to modify any production
path in this ratification change.

| Future work item | Required? | Bounded change |
| --- | --- | --- |
| `TrajectoryWriterHandoffCoordinator` sidecar component | YES | New typed, scope-only coordinator schema, lock namespace, transitions, and immutable receipts. |
| Legacy writer client | YES | Bind every production `MemoryGraph` trajectory sink to registration, quiescence acknowledgement, and guarded writes; no direct production sink bypass. |
| Native writer client | YES | Bind private process-state and shared request-state evidence runtimes to the coordinator before genesis/frame/classification/tail effects. |
| Write-path fence | YES | Guard `TrajectoryV2Writer`, `TrajectoryLogger`, and native classification-event effects with generation/session verification and intent reconciliation. |
| Recovery | YES | Implement durable phase/intent reconciliation and native-session fencing after process/service/machine restart. |
| Root disposition adapter | YES | Add a trajectory aggregate verifier/receipt consumer only; it must not execute a handoff or alter another disposition. |
| P7 verifier | YES | Require the aggregate trajectory receipt/current-native-session check alongside the existing class-A/class-C gates. |

```text
NEW_OWNER_COMPONENT_REQUIRED               = YES
LEGACY_WRITER_CHANGE_REQUIRED              = YES
NATIVE_WRITER_CHANGE_REQUIRED              = YES
TRAJECTORY_WRITE_PATH_FENCE_REQUIRED       = YES
RECOVERY_CHANGE_REQUIRED                   = YES
ROOT_DISPOSITION_ADAPTER_CHANGE_REQUIRED   = YES
P7_VERIFIER_CHANGE_REQUIRED                = YES
```

## Internal adversarial review

`CLAUDE_REVIEW=UNAVAILABLE`. The following bounded internal review is the
required substitute.

| Challenge | Finding and contract response |
| --- | --- |
| Can a legacy process write after handoff? | Not after a guarded writer sees the durable generation mismatch. An unguarded deployment blocks the handoff at the P2/coverage predecessor; it is not allowed to coexist with native authority. |
| Can two native processes believe they own one scope? | At most one session record is current under the scope lock. Native-session replacement increments the fence before the replacement writes; the former session then refuses. |
| Can a coordinator crash create ambiguous authority? | No. The durable phase/generation and intent ledger determine recovery. An unsettled intent blocks fence/admission rather than guessing. |
| Can exact retry duplicate the transition? | No. Operation identity, P6/core/scope bindings, and terminal receipt must all match exactly; matching replay returns the receipt and conflicts refuse. |
| Can a partial handoff satisfy P7? | No nonterminal phase, ambiguous intent, missing current native session, missing scope receipt, or aggregate mismatch is P7-eligible. |
| Is the new authority broader than trajectory ownership? | No. Its schema, scope key, and APIs contain only writer coordination records and have no selector, memory, Character, motif, proposal, or general process-control operation. |
| Does restart preserve fencing? | Yes. The durable generation survives; recovery must re-fence/revalidate a native session before it writes. No Python memory or timeout establishes authority. |
| Does the protocol require post-P6 rollback? | No. It only advances legacy-to-native authority. Any unsafe state blocks and requests review without restoring P5/pre-P6 state. |

## Validation and required result record

```text
STARTING_HEAD                              = 0169897add00f2a36203fc347cf7ca88a15b7f51
ORIGIN_MAIN_AT_START                       = 0169897add00f2a36203fc347cf7ca88a15b7f51
TRACKED_WORKTREE_AT_START                  = CLEAN

REAL_ROOT_MUTATION                         = NONE
REAL_ROOT_UNCHANGED                        = YES
REAL_P7_EXECUTED                           = NO

LEGACY_TRAJECTORY_WRITER_COUNT / CLASSES   = 1 family / 4 construction paths / 2 formats
NATIVE_TRAJECTORY_WRITER_COUNT / CLASSES   = 1 family / 2 lifecycle bindings / 2 formats
WRITER_EXCLUSIVITY_KEY                     = data root + RootScopeKey + source namespace + artifact root

TRAJECTORY_HANDOFF_OWNER                   = TrajectoryWriterHandoffCoordinator
TRAJECTORY_HANDOFF_OWNER_AUTHORITY         = scope-bound writer generation/fence/admission/receipt coordination only
TRAJECTORY_HANDOFF_OWNER_STORAGE           = substrate/trajectory_writer_handoff/authority.sqlite + scope locks
LEGACY_QUIESCENCE_MECHANISM                = P2 recheck/census + registrations + acknowledgements + settled ledger + fence
LEGACY_REENTRY_AFTER_FENCE                 = REFUSED
NATIVE_ADMISSION_MECHANISM                 = exact-P6/core/scope-bound coordinator transaction
WRITE_AUTHORITY_CHECK                      = locked durable generation/session check immediately before every effect
HANDOFF_STATE_MACHINE                      = LEGACY_AUTHORITATIVE -> QUIESCING -> LEGACY_QUIESCED ->
                                             NATIVE_ADMITTING -> NATIVE_AUTHORITATIVE -> HANDOFF_COMPLETE

IDEMPOTENCE_DEFINED                        = YES
PARTIAL_FAILURE_DEFINED                    = YES
RESTART_RECOVERY_DEFINED                   = YES
HANDOFF_RECEIPT_CONTRACT                   = defined per scope
AGGREGATE_TRAJECTORY_RECEIPT_CONTRACT      = defined over exact P6 materialized scope census
TRAJECTORY_CHARACTER_ORDER_DEPENDENCY      = NO

NEW_OWNER_COMPONENT_REQUIRED               = YES
LEGACY_WRITER_CHANGE_REQUIRED              = YES
NATIVE_WRITER_CHANGE_REQUIRED              = YES
TRAJECTORY_WRITE_PATH_FENCE_REQUIRED       = YES
RECOVERY_CHANGE_REQUIRED                   = YES
ROOT_DISPOSITION_ADAPTER_CHANGE_REQUIRED   = YES
P7_VERIFIER_CHANGE_REQUIRED                = YES

DUAL_WRITE_POSSIBLE                        = NO
DUAL_READ_AUTHORITY_POSSIBLE               = NO production grant
AUTOMATIC_POST_P6_ROLLBACK                 = NO
NEW_HIDDEN_AUTHORITY                       = NO
MODEL_D_CHANGED                            = NO
CERTIFIED_REFUSAL_SEMANTICS_CHANGED        = NO

FOCUSED_TESTS                              = tests/test_real_root_disposition_owner_contract.py;
                                             tests/test_trajectory_writer_handoff_contract.py
CLAUDE_REVIEW                              = UNAVAILABLE (internal adversarial matrix recorded above)

TRAJECTORY_HANDOFF_CONTRACT                = RATIFIED
ROOT_DISPOSITION_OWNER_CONTRACT            = RATIFIED
NEXT_AUTHORIZATION_BOUNDARY                = implement the ratified trajectory-handoff and Character-baseline
                                             disposition owners; no P7 authority is granted
```
