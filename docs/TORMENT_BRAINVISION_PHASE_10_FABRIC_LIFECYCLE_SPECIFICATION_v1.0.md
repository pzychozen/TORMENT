# TORMENT Brainvision Phase 10 Fabric Lifecycle Specification v1.0

## Status and authority

**FROZEN PRE-IMPLEMENTATION PHASE-10 SPECIFICATION**

Phase 10 freezes Brainvision lifecycle hosting, runtime ownership,
configuration/sidecar transactions, recovery, and shutdown behavior. It does
not reopen Phases 0-9.

## 1. Ownership boundary

Phase 10 owns:

1. ordinary-agent existence proof;
2. per-agent synchronization;
3. Brainvision configuration creation/deletion authorization;
4. disabled profile reconfiguration authorization;
5. enable, suspend, resume, reset, and disable;
6. process-local Brainvision runtime ownership and active/suspended
   reconstruction;
7. configuration/sidecar transaction ordering, recovery-matrix execution,
   watermark repair, and orphan-sidecar deletion;
8. shutdown flush behavior; and
9. the internal locked transaction boundary needed by Phase 11 and the
   internal runtime snapshot boundary needed by Phase 12.

Phase 10 does not own observation-envelope parsing, observation identity,
replay-admission policy, descriptor/VHE successor mathematics, public ingress,
or public projection/sink APIs. It does not own or integrate with MemoryGraph,
native memory, kernel state, CognitiveCore, SRG, Hivermind, or model/prompt
systems.

## 2. Known-agent authority and lock order

The sole ordinary-agent existence authority is:

~~~text
IdentityStore.load(workspace_id, agent_id)
~~~

Every externally initiated Brainvision lifecycle or internal operation follows
this exact order:

1. strictly validate workspace_id and agent_id without allocation;
2. call IdentityStore.load;
3. if absent, fail unknown_agent;
4. if malformed or if the returned identity does not exactly match the
   requested workspace/agent pair, fail agent_identity_invalid;
5. only then obtain AgentLockManager.agent_lock(workspace_id, agent_id);
6. acquire that RLock;
7. reload and revalidate ordinary-agent identity while holding the lock; and
8. only then access configuration, sidecar, runtime, or lifecycle state.

Brainvision existence checks must not call TormentFabric.create_agent() or
TormentFabric.get_workspace(). Unknown agents create no lock-registry entry,
workspace, ordinary-agent state, Brainvision artifact, or runtime.

Only the existing AgentLockManager.agent_lock(workspace_id, agent_id) is the
lawful synchronization boundary. It is held throughout every Phase-10
lifecycle transaction and future Phase-11 commit transaction. No workspace
lock is acquired as a prerequisite and no workspace-lock-to-agent-lock
dependency is introduced.

## 3. Runtime ownership and state epoch

BrainvisionLifecycleManager owns the process-local registry:

~~~text
(workspace_id, agent_id) -> BrainvisionRuntime
~~~

BrainvisionRuntime conceptually contains:

~~~text
configuration: BrainvisionConfigurationV1
vhe_state: VheState
visual_clock: VisualClock
~~~

No Brainvision runtime state is placed in AgentIdentity, CharacterState,
MemoryGraph, kernel state, or native checkpoints.

The mandatory state-epoch invariant is:

~~~text
runtime.vhe_state represents exact recursive state at
runtime.visual_clock.committed_active_time_ns.
~~~

For an active runtime, later process-local elapsed time exists only through the
clock origin until an operation stages and commits it. VHE state is never
evolved by absolute total active time. When current active time is resolved:

~~~text
delta_active_time_ns =
    resolved_committed_active_time_ns - prior_committed_active_time_ns
~~~

Only that delta is supplied to frozen F free evolution or successor derivation.

The manager owns/injects the monotonic source for all VisualClock instances.
The production default is time.monotonic_ns; tests may inject a deterministic
source.

Active reconstruction uses:

~~~text
VisualClock.from_active(
    committed_active_time_ns=sidecar.committed_active_time_ns
)
vhe_state = sidecar.vhe_state
configuration = reconciled durable configuration
~~~

Suspended reconstruction uses VisualClock.from_frozen at the same sidecar time
and retains the reconstructed runtime in process for frozen projection/snapshot
reads. Disabled configuration has no runtime.

## 4. Staged active clock and state

Preparing a durable active-state write must not mutate the authoritative live
runtime. The manager constructs a staged clock from the live clock's prior
committed_active_time_ns, current process_local_origin_ns, and the same
manager-owned monotonic source. It calls resolve_and_rebase() only on that
staged clock. Let:

~~~text
new_time = staged_clock.committed_active_time_ns
old_time = live_clock.committed_active_time_ns
delta = new_time - old_time
~~~

The staged VHE state is derived using exactly delta. The required durable write
occurs before staged state is adopted according to the operation-specific rules
below. Thus a failed sidecar write leaves the original live active runtime
untouched.

## 5. Configuration creation, deletion, and disabled reconfiguration

Configuration creation is explicit and separate from enable:

~~~text
configure_brainvision(
    workspace_id,
    agent_id,
    stream_identity,
    adapter_contract_id,
    theta,
)
~~~

It requires a known ordinary agent, held agent lock, absent configuration,
absent sidecar, and absent runtime. It builds
fresh_disabled_brainvision_configuration(...) and atomically writes it.
Configuration absence is not equivalent to disabled.

Configuration deletion is an explicit new-lineage operation, legal only when
configuration exists and is disabled, recovery is complete, runtime is absent,
and sidecar is absent. It deletes only the contained configuration.json
artifact. An empty Brainvision directory may remain and has no lifecycle or
lineage authority. A later creation starts a new lineage with watermark -1.
Deletion is not disable.

Disabled profile reconfiguration is legal only with disabled configuration,
absent runtime, and absent sidecar after recovery. The candidate retains stream,
adapter contract, watermark, operator/projection identities, and modulation
schemas/mapping. It changes only theta and modulation_profile_id, validates
through Phase-8 replacement compatibility, and atomically replaces the
configuration. Active or suspended profile changes are forbidden.

## 6. Lazy recovery and recovery matrix

There is no Fabric-wide startup scan. Recovery runs lazily, under the known
agent lock, on first Brainvision lifecycle/internal access for that agent. An
existing in-process runtime is validated against durable configuration/sidecar
lineage before use.

| Durable artifacts | Required outcome |
| --- | --- |
| no configuration + no sidecar | configuration_absent; no mutation |
| no configuration + sidecar | sidecar_integrity_failure; no mutation and no deletion |
| disabled configuration + no sidecar | normal disabled state; no runtime |
| disabled configuration + sidecar | validate lineage, apply disabled-orphan precedence, delete orphan, remain disabled with no runtime |
| active/suspended configuration + no sidecar | sidecar_missing hard failure; no runtime and no silent initialization |
| active/suspended + EQUAL | normal reconstruction |
| active/suspended + SIDECAR_AHEAD | repair configuration watermark upward, then reconstruct |
| active/suspended + CONFIG_AHEAD | config_ahead hard failure; no mutation and no runtime |

For an absent runtime, disabled configuration constructs none; active
configuration reconstructs active; and suspended configuration reconstructs
frozen runtime.

## 7. Disabled-orphan precedence and sidecar-ahead repair

The generic CONFIG_AHEAD hard failure applies to active/suspended continuation.
A disabled configuration with a sidecar is an orphan-cleanup branch with this
exact precedence:

- identity mismatch: integrity failure; do not delete;
- sidecar sequence greater than configuration watermark: atomically repair the
  configuration watermark upward, then delete the orphan;
- equal sequence: delete the orphan; and
- configuration watermark greater than sidecar sequence: deletion is permitted
  because configuration watermark >= sidecar watermark satisfies the frozen
  disable safety condition.

After lawful deletion, configuration remains disabled and runtime is absent.

For SIDECAR_AHEAD repair, after exact identity compatibility is established, the
candidate configuration changes only:

~~~text
last_accepted_source_sequence = sidecar.accepted_source_sequence
~~~

Lifecycle status and all lineage/profile identities are unchanged. Phase-8
replacement compatibility is validated and the candidate is atomically written.
The sidecar is not rewritten and no observation is replayed.

## 8. Enable

Enable from disabled performs disabled recovery/orphan cleanup first, then
requires durable disabled configuration and absent runtime:

1. build fresh_vhe_sidecar(configuration);
2. atomically write that sidecar;
3. build active-status configuration and validate replacement compatibility;
4. atomically write active configuration; this is the durable lifecycle commit
   point; and
5. only after commit, construct active runtime using fresh sidecar state,
   VisualClock.from_active(committed_active_time_ns=0), and active
   configuration.

If sidecar writing fails, disabled configuration remains authoritative and
runtime remains absent. If sidecar writing succeeds but active-status writing
fails, disabled configuration remains authoritative, runtime remains absent,
and the sidecar is a removable orphan. If active status commits but process
runtime allocation fails, durable state is active, runtime remains absent,
recovery_required/runtime_allocation_failure is raised, and the next access
reconstructs from active configuration and valid sidecar.

Active enable first validates normal active recovery, then is a no-op only when
durable configuration, sidecar, and runtime all match. It writes nothing.
Suspended enable is an invalid transition; use resume.

## 9. Suspend

Suspend is active-only. Prepare staged active clock/state under the staged
rule. Let cutoff be the staged resolved active time and let:

~~~text
delta = cutoff - live_runtime.visual_clock.committed_active_time_ns
~~~

Evolve only F by delta; S and R remain unchanged. Build staged sidecar with
that VHE state, committed_active_time_ns = cutoff, and unchanged accepted
sequence. Then:

1. atomically write staged sidecar; and
2. atomically write suspended-status configuration; this is the suspend commit
   point.

If sidecar writing fails, live runtime/configuration remain active and
unchanged. If sidecar writing succeeds but status writing fails, configuration
remains active, but the runtime adopts staged VHE state and staged active clock
that continues from its rebased origin. This prevents reapplication or double
counting of the elapsed interval.

After successful status write, configuration is suspended, runtime state is
the staged VHE state, and the active staged clock is replaced with:

~~~text
VisualClock.from_frozen(committed_active_time_ns=cutoff)
~~~

Do not call freeze() after durable cutoff because a second sample could change
persisted time. Suspended suspend is a validated idempotent no-op; disabled
suspend is invalid.

## 10. Resume

Resume is suspended-only and requires valid reconciled sidecar/runtime:

1. atomically write active-status configuration; this is the commit point; and
2. after durable commit establish a new active origin with
   VisualClock.from_active(committed_active_time_ns=sidecar.committed_active_time_ns).

No sidecar rewrite occurs and frozen downtime is not added. If runtime
activation fails after active status commits, durable lifecycle remains active,
runtime is dropped, recovery_required/runtime_allocation_failure is raised, and
future access reconstructs active runtime. Active or disabled resume is invalid.

## 11. Reset

Reset is active- or suspended-only. It preserves configuration status, stream,
adapter contract, watermark, identities, and profile. Build a fresh sidecar
from that configuration with fresh VHE state, committed time zero, and accepted
sequence copied from the configuration watermark. Atomically replace the
sidecar; this is the reset commit point.

After success, active runtime receives fresh VHE state and
VisualClock.from_active(committed_active_time_ns=0); suspended runtime receives
fresh VHE state and VisualClock.from_frozen(committed_active_time_ns=0). There
is no configuration write. A failed replacement leaves live runtime and
configuration unchanged. Disabled reset is invalid.

## 12. Disable

Disable is active- or suspended-only after normal recovery. It requires
identity compatibility and:

~~~text
configuration watermark >= sidecar accepted sequence
~~~

Then:

1. atomically write disabled-status configuration; this is the commit point;
2. attempt contained sidecar deletion; and
3. deallocate runtime regardless of deletion outcome.

If configuration-status writing fails, the prior active/suspended lifecycle,
sidecar, and runtime remain valid. If disabled status commits but sidecar
deletion fails, durable lifecycle is still disabled, runtime is deallocated,
and a post-commit durability_failure/cleanup failure is recorded or raised.
The orphan remains for later disabled recovery. No fourth lifecycle status is
introduced.

Disabled disable first performs disabled recovery, then is an idempotent
disabled no-op.

## 13. Accepted-observation internal transaction

Phase 10 does not parse or validate Phase-2 observations. It exposes a locked
internal active transaction for Phase 11. The agent RLock remains held across
snapshot, Phase-11 replay/admission decision, successor derivation, and durable
commit.

The transaction prepares staged active cutoff/clock without changing live
runtime and exposes exactly enough data for Phase 11 to derive a successor:

- base VheState;
- prior committed active time;
- cutoff active time and elapsed delta;
- configuration/profile; and
- current replay watermark.

Phase 11 returns an already-derived valid successor VHE state and accepted
source sequence. Phase 10 must not parse the observation or derive VHE itself.

The Phase-10 commit receives successor state, sequence, and the transaction's
exact staged cutoff/clock, then:

1. constructs and atomically writes sidecar with successor state, cutoff time,
   and new accepted sequence;
2. atomically writes configuration with the new watermark;
3. only after both writes succeed, adopts successor state, staged active clock,
   and updated configuration; and
4. only then returns committed success to Phase 11.

If sidecar writing fails, configuration and live runtime remain unchanged. If
sidecar succeeds but configuration writing fails, do not reapply successor, do
not expose success or sink behavior, drop this agent's process-local runtime,
raise recovery_required, and refuse new observations until lazy recovery
repairs SIDECAR_AHEAD and reconstructs runtime.

## 14. Internal projection/snapshot support

Phase 10 may expose an internal locked runtime snapshot for Phase 12. An active
snapshot accounts for local elapsed active time through frozen Phase-4 pure
as-of evolution or an equivalent exact elapsed representation. A suspended
snapshot uses frozen committed state/time. Disabled snapshots are refused.

Phase 10 implements no public projection, read, or sink API.

## 15. Shutdown and Fabric hosting

BrainvisionLifecycleManager exposes a non-throwing idempotent shutdown hook.
TormentFabric.close() invokes it before existing SQLite, graph, kernel, and
temporary-directory cleanup.

For each active runtime, shutdown:

1. creates staged clock/state from live runtime;
2. resolves staged clock;
3. evolves F by staged time minus live committed time;
4. constructs sidecar at staged committed time;
5. performs exactly one best-effort atomic sidecar write;
6. writes neither configuration status nor configuration watermark;
7. performs no altered retry;
8. records Brainvision-local durability failure if writing fails; and
9. removes runtime regardless.

Suspended runtime is already durably frozen: no sidecar flush, then remove it.
Disabled state has no runtime. One shutdown failure cannot prevent other
Brainvision runtimes from tearing down, and Brainvision shutdown must never
raise through TormentFabric.close().

The minimum future production surface is:

~~~text
NEW:    brainvision/lifecycle.py
MODIFY: torment_service/fabric.py
~~~

After self.ident_store and self.locks exist, Fabric constructs one inert manager
with data root, the existing IdentityStore, and the existing AgentLockManager,
preferably as self.brainvision_lifecycle. Construction does no filesystem scan,
configuration creation, runtime creation, or agent creation. At the beginning
of close(), Fabric uses defensive getattr and the non-throwing manager shutdown
hook before existing cleanup. Fabric close remains idempotent.

## 16. Error model and isolation

Phase 10 has a lifecycle error family distinct from Phase-8/9 schema errors,
with at least:

~~~text
unknown_agent
agent_identity_invalid
configuration_absent
invalid_lifecycle_transition
sidecar_missing
sidecar_integrity_failure
configuration_sidecar_incompatible
config_ahead
recovery_required
runtime_allocation_failure
durability_failure
~~~

Errors after a durable lifecycle commit must explicitly report that fact; an
exception must never imply rollback. Preserve Phase-8/9 validation and storage
errors as chained causes where useful.

The lifecycle manager receives only data root, IdentityStore,
AgentLockManager, and monotonic source. It must not read or write MemoryGraph,
native memory retrieval, TriOcta kernel, CharacterSeed, CharacterState,
CognitiveCore, SRG, Hivermind, or LLM prompt/model paths.

## 17. Frozen future test plan

Future Phase-10 tests must cover:

1. every lifecycle matrix edge, idempotent transition, and invalid transition;
2. unknown-agent pre-lock refusal, malformed/mismatched identity, and identity
   disappearance between precheck and locked recheck;
3. configuration creation, explicit deletion/new lineage, and disabled profile
   reconfiguration;
4. active/suspended cold reconstruction and disabled no-runtime reconstruction;
5. every recovery-matrix branch;
6. disabled orphan equal, sidecar-ahead repair, config-ahead safe deletion, and
   identity-mismatch refusal;
7. active/suspended equal, sidecar-ahead repair, and config-ahead hard failure;
8. enable sidecar-write failure, status-write failure, and post-commit runtime
   allocation failure;
9. suspend exact staged cutoff, delta rather than absolute-time F evolution,
   sidecar-write preservation, status-write staged-active adoption, successful
   frozen cutoff, and no double sampling/counting;
10. resume downtime exclusion, status commit before active origin, and
    post-commit allocation failure;
11. active/suspended reset, sidecar-failure preservation, and watermark
    preservation;
12. disable status failure, deletion success, post-commit deletion failure,
    runtime deallocation, and later orphan cleanup;
13. accepted-observation lock scope, sidecar-first/config-second ordering,
    sidecar-failure preservation, configuration-failure runtime drop/recovery,
    no reapplication, and no sink before full commit;
14. active exact staged shutdown flush, flush failure, no altered retry,
    suspended no-flush, native Fabric-close continuation, and repeated-close
    idempotence; and
15. static isolation: no memory/kernel/cognition/SRG/Hivermind/model imports,
    no Phase-11 observation parser, and no Phase-12 public sink/read API.

## 18. Claim ceiling

Phase 10 does not establish direct visual ingress, observation-admission
correctness, public projection/sink correctness, physical vision accuracy, LLM
 usefulness, memory/cognitive integration, complete v1a qualification, or v1b
 integration.
