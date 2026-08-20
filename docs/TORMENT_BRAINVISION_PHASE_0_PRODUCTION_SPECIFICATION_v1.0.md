# TORMENT Brainvision — Phase 0 Production Specification v1.0

## Status and authority

**FROZEN PRE-IMPLEMENTATION SPECIFICATION**

This is the canonical, self-contained Phase 0 specification for the optional
TORMENT Brainvision subsystem. It consolidates the Phase 0 candidate, the v1.1
reconciliation amendments, and the final lifecycle/crash-recovery amendment.
Earlier Phase 0 candidate or amendment wording is not authoritative where it
differs from this document.

Phase 0 authorizes no production implementation. It does not authorize
Brainvision engine classes, DTOs, Fabric registries, ingress routes, or changes
to existing production behavior.

The Phase 0 completion state is `BRAINVISION_PHASE0_SPEC_FROZEN`.

---

## 1. Product objective and boundary

Brainvision is an optional, per-agent sibling subsystem that preserves
history-sensitive visual context:

> The current visual observation does not completely determine the agent's
> Brainvision projection. What the agent has visually witnessed can remain
> relevant after the present scene returns to a previous apparent state.

Brainvision does not represent emotion. Affective or character behavior
downstream of Brainvision belongs to later governed TORMENT integration.

### v1a

v1a is internal engine qualification only. Its eventual scope is typed
firsthand visual ingress, Brainvision-owned active visual time, a deterministic
Visual History Engine (VHE), Fast Trace, a dynamical write gate, Persistent
Context, a bounded semantic/open-event register, Brainvision-specific character
modulation, bounded relational projection, Brainvision-owned configuration and
state persistence, Fabric lifecycle hosting, direct Fabric visual ingress, and
diagnostic/null sinks only.

v1a does not create durable memory, write to MemoryGraph, mutate CognitiveCore
or native kernel state, depend on SRG, mutate Hivermind or collective state,
use ordinary `fabric.ingest`, use Spine, construct prompts, invoke an LLM, or
expose raw VHE state to a model.

### v1b

v1b is later governed integration. It owns any read-side composition, memory,
model, or other consumer integration intentionally excluded from v1a. No v1b
consumer is required to qualify v1a.

### Existing-system invariant

When Brainvision is absent or disabled, existing TORMENT semantics and existing
subsystem state transitions remain unchanged. A disabled agent has no allocated
VHE runtime state, VHE state sidecar, visual state update, projection, or
visual-processing diagnostic event. A Brainvision configuration artifact may
exist while disabled.

When active, Brainvision may add only bounded same-agent lock contention,
Brainvision-specific filesystem I/O, and Brainvision-specific validation or
failure surfaces. Those effects remain isolated from unrelated subsystem state.

---

## 2. Product horizon and active visual time

Freeze:

`T_PRODUCT_V1 = 300.0 seconds of active visual time after retained-event onset`

This is a product requirement, not a value selected from an observed operator.
It is not reduced when an implementation fails. Phase 0 assumes no universal
exponential relationship among horizon, decay, write amplitude, and projection
quantum.

### Active visual time

Visual time is Brainvision-owned active experienced visual time. It is not
camera-frame count, observation count, service request count, `fabric.ingest`
count, LLM-turn count, or persistent wall-clock time.

While active:

`visual_time = persisted_active_time + process-local monotonic elapsed time`

Production uses a monotonic clock. A deterministic injectable test/replay clock
is mandatory. A live process-local monotonic origin is never serialized.
Process downtime and suspension do not advance visual time in v1a; realtime
catch-up is deferred.

The monotonic origin is rebased whenever active accumulation begins or
committed active time changes: enable, accepted-observation commit, resume,
active reset, active-state reload, and successful shutdown-time state resolution
where applicable. Suspend first resolves and commits active visual time, then
freezes it. Suspended reset sets frozen visual time to zero. Disable destroys
VHE continuation state and does not preserve visual time for later continuation.

Projection reads are pure. They may calculate an as-of state but never mutate
stored F/S/R, advance committed visual time, rewrite a sidecar, or alter replay
state. Read scheduling over the same observation and lifecycle schedule must
leave committed VHE state `BIT_IDENTICAL` and yield identical later canonical
projections.

---

## 3. Stream, ordering, identity, and replay

v1a supports exactly one canonical firsthand visual stream per agent.
Multi-camera or multi-stream merging is upstream perception work. Each
configured Brainvision agent has one immutable `stream_identity` for the
lifetime of its v1a configuration; rebinding is outside v1a.

The adapter provides stream identity, strictly increasing `source_sequence`,
canonical `observation_id`, optional capture timestamp as provenance, an
observation payload, and adapter/provenance metadata. The authoritative v1a
ordering key is `source_sequence` within the canonical stream. Capture
timestamps are provenance only; equal timestamps and sequence gaps are valid.

`observation_id` is deterministically derived from or validated against
`(stream_identity, source_sequence)`. Phase 2 freezes the exact canonical
encoding or hash. This binding, and its injectivity for the canonical stream,
are Phase 0 invariants.

### Dynamically inert metadata

`source_sequence`, `observation_id`, `world_event_id`, and capture timestamp
may be used for validation, ordering, replay, provenance, correlation, or
deterministic references. They must not affect F/S/W numerical dynamics, gate
values, magnitudes, decay parameters, or weights.

### Replay rule

The configuration artifact persistently retains `stream_identity` and
`last_accepted_source_sequence`. The high-water mark survives reset,
suspension, reload, disable, and disable-to-enable.

There is no payload-history ledger in v1a. For an incoming observation:

- if `source_sequence <= last_accepted_source_sequence`, return
  `REFUSED_REPLAY` before VHE mutation, do not invoke a sink, and preserve VHE
  and persisted state `BIT_IDENTICAL`;
- if `source_sequence > last_accepted_source_sequence`, require the supplied
  identity to match the frozen canonical stream/sequence identity; otherwise
  return `INVALID_OBSERVATION_ID` without mutation.

Replay protection lasts for the same persisted configuration/agent lineage.
Explicit configuration deletion or agent destruction/recreation creates a new
lineage and is outside v1a continuity guarantees. Brainvision adds no agent
deletion lifecycle.

---

## 4. Firsthand provenance and semantic boundary

Only an admitted typed `FIRSTHAND_VISUAL` observation may mutate VHE state.
User language, reported observation, retrieved memory, tool output, model
output, collective/Hivermind echo, ordinary TORMENT ingest, and Spine task
content cannot mutate the VHE.

This is a structural boundary, enforced by typed provenance validation, direct
Brainvision ingress, import/call-boundary tests, and runtime guards. v1a does
not need a vacuous hearsay mutation test because it has no hearsay/retrieval
mutation API. Read-side hearsay composition belongs exclusively to v1b.

---

## 5. Phase-0 fixtures and product acceptance

Phase 2 freezes three exact canonical serialized, valid, low-level descriptor
fixtures before Phase 4 operator design:

- `d0`: neutral descriptor;
- `dA`: retained-event descriptor; and
- `dB`: second event descriptor.

They are pairwise distinguishable, contain no semantic event class, and are
valid under the Phase-2 descriptor schema. Phase 4 may not redefine them to
suit the operator.

### Retained-history fixture

H0 is `d0` at t=0, t=1, and t=2. H1 is `d0` at t=0, `dA` at t=1, and `d0` at
t=2. At t=301, request a pure projection read. This is exactly 300 active
visual seconds after the retained event at t=1.

The histories have equal final descriptor, visual time, observation count,
sequence structure, and no semantic class. The relevant current-activity
representation must be equal while a field bound to `RETAINED_HISTORY_ROLE`
remains distinguishable. R cannot satisfy this fixture.

### Order-sensitive fixture

O1 is `d0, dA, dB, d0` at t=0,1,2,3. O2 is `d0, dB, dA, d0` at the same times.
Semantic class is absent. At a common read time, current activity must be equal
and one preregistered non-semantic history-sensitive role must differ.

### Invariance and neutral fixtures

Metadata-only histories differing only in dynamically inert metadata, initially
`world_event_id`, require F/S/W and all dynamical projection fields to be
`BIT_IDENTICAL`.

The neutral/no-write fixture is the canonical fresh-or-reset neutral trajectory
with continued `d0` input. It does not claim that `d0` causes zero write from
every possible preceding state. Phase 4 freezes and tests each exact no-write
or no-change claim made for that all-neutral trajectory.

---

## 6. Exact relations and projection roles

Only two named relations are used in v1a acceptance tests.

### `BIT_IDENTICAL`

For canonical serialized state, exact bytes match. For pure operator state
before serialization, the frozen scalar or array representation matches
bit-for-bit. It is used for invariance, refused replay, pure-read behavior,
deterministic reload continuation, and declared exact no-change cases.

### `WITHIN_PROJECTION_QUANTUM`

This is equality of canonical projection representations, not raw floating
tolerance. Phase 5 freezes every continuous field's domain, normalization,
canonical quantizer, resolution, clipping/saturation behavior, and
integer/canonical encoded representation. Categorical or structural fields use
exact canonical codes.

For a preregistered relevant field set, projections are
`WITHIN_PROJECTION_QUANTUM` exactly when every canonical encoded field agrees.
They are distinguishable when at least one relevant encoded field differs.

Phase 5 freezes concrete fields for these roles:

- `CURRENT_ACTIVITY_ROLE`;
- `RETAINED_HISTORY_ROLE`;
- `PRESENT_HISTORY_RELATION_ROLE`;
- `TRAJECTORY_ROLE`;
- `OPEN_EVENT_ROLE`; and
- `RECURRENCE_ROLE`.

Each acceptance test freezes its relevant field set before result inspection.
Retained history requires equal current activity and a retained-history
difference. Order sensitivity requires equal current activity and a named
history-sensitive non-semantic role. Dedicated semantic-register and recurrence
fixtures require their respective roles to function; neither may be constant
merely because the low-level fixture has no semantic class.

No Phase-5 present-versus-history field may hide another recursive baseline
estimator. Any necessary new recursive state reopens Phase 4 and requires
explicit ownership, definition, persistence, identity, and tests.

---

## 7. Semantic and dynamical isolation

The write gate W cannot read semantic event class, R, `world_event_id`, text,
embeddings, memory, native kernel state, CognitiveCore, SRG, Hivermind, or
model output. Semantic class may update R only after W is computed.

Changing only semantic class may alter R but leaves F/S/W `BIT_IDENTICAL`.
Changing only `world_event_id` leaves all VHE dynamics `BIT_IDENTICAL`. A
low-level-only observation cannot create an R entry. Therefore R is empty in
the low-level retained-history fixture unless a separately admitted semantic
observation occurred.

---

## 8. Character modulation

Phase 0 does not define final modulation axes or `THETA_V1`. It freezes this
contract:

- a neutral `theta_0` exists and may dispatch directly to the baseline path;
- `theta_0` reproduces the baseline operator `BIT_IDENTICAL`;
- modulation is Brainvision-specific and does not change VHE schema or
  dimensions;
- v1a has no automatic CharacterSeed-to-theta derivation and no global process
  flag for Brainvision modulation;
- every non-neutral accepted axis has a preregistered direction and minimum
  nonzero effect; and
- the product horizon holds across the full admitted modulation domain.

Phase 7 freezes and versions axes, `THETA_V1` domain, profile/schema identity,
operator mapping, directional predictions, minimum effects, and either an
analytic coverage proof or finite validation grid before result inspection. The
domain, mapping, effect criterion, or grid cannot be narrowed after failures
without a new identity, renewed validation, and required reauthorization.

At least one accepted non-neutral profile must yield a projection-visible
difference of at least one frozen quantum on its preregistered fixture while
using the same firsthand history and current observation and preserving schema
and the product horizon.

---

## 9. Rate-invariance claim ceiling

v1a does not claim arbitrary camera-frame-rate invariance. Phase 4 freezes its
actual free-evolution law and only the elapsed-time composition properties
claimed for that law. Phase 0 imposes no blanket exponential or semigroup law.

The required invariances are those established for the frozen operator,
pure-read schedule independence, and deterministic replay under the same
ordered observation stream, deterministic clock schedule, lifecycle-operation
schedule, configuration, and frozen operator/projection/modulation identities.
Per-observation impulses, event count, recurrence count, sampling patterns,
and camera frame rate are not generally rate-invariant in v1a.

---

## 10. Lifecycle state machine

Runtime states are `disabled`, `active`, and `suspended`. Reset is an operation.

| Current state | Operation | Result |
| --- | --- | --- |
| disabled | enable | active with fresh VHE state |
| active | enable | active only when configuration matches |
| suspended | enable | error; use resume |
| active | suspend | suspended with persisted frozen state |
| suspended | suspend | idempotent suspended |
| disabled | suspend | error |
| suspended | resume | active |
| active or disabled | resume | error |
| active | reset | active with fresh state and zero active visual time |
| suspended | reset | suspended with fresh frozen state and zero visual time |
| disabled | reset | error |
| active or suspended | disable | disabled and no VHE sidecar |
| disabled | disable | idempotent disabled |

Projection reads are allowed while active and while suspended at frozen visual
time, and refused while disabled. Observation updates may proceed only while
active; they are refused while suspended or disabled.

Reset never changes stream identity or lowers the replay high-water mark.
Disable deallocates runtime and deletes the VHE sidecar while preserving
configuration, stream identity, and replay watermark. Thus `reset != disable`.

---

## 11. Configuration and state ownership

Brainvision has two separate artifacts:

1. **Configuration artifact** is authoritative for lifecycle status and replay
   lineage. It contains capability status, stream identity, source-sequence
   high-water mark, configuration schema identity, expected operator and
   projection identities, and modulation profile/schema identity.
2. **VHE state sidecar** is authoritative for recursive VHE continuation state,
   exact persisted numerics, accumulated active visual time, and its copy of
   the accepted source sequence. Lifecycle status is not independently
   authoritative in the sidecar.

The configuration artifact may exist while disabled. A disabled agent must not
retain a VHE state sidecar. Neither Brainvision artifact is stored in
AgentIdentity, CharacterSeed, CharacterState, or native checkpoint payload.

Every recursive numeric value required for continuation round-trips its exact
underlying IEEE bit pattern. The final Brainvision-owned on-disk encoding is
selected in Phase 9. JSON decimal text is valid only if independently proven
bit-exact for the actual frozen representation. Projection quantization never
substitutes for lossless internal-state persistence.

All continuation-relevant identities are individually checked. Missing,
corrupt, or incompatible required active/suspended state is a hard failure.
v1a has no migration subsystem.

---

## 12. Persistence transactions and recovery

All artifact writes use contained paths and atomic replacement. A successful
configuration-status write is the lifecycle commit point where stated below.

### Enable

Enable requires disabled configuration. First remove any stale orphan sidecar,
then build a fresh sidecar with the durable configuration high-water mark,
write it atomically, and atomically change configuration status to `active`.
If interrupted before the status write, configuration remains disabled and the
sidecar is a removable orphan.

### Suspend

Resolve and commit active visual time into the sidecar, atomically write the
sidecar, then atomically change configuration status to `suspended`. The status
write is the commit point. An interrupted suspend before that point remains
active.

### Resume

Resume requires suspended configuration and a valid sidecar. Atomically change
status to `active` and rebase the process-local monotonic origin. Resume alone
does not require a sidecar rewrite.

### Reset

Use the existing durable configuration watermark to build a fresh recursive
sidecar carrying that same watermark and zero active visual time. Atomically
replace the sidecar. This is the reset commit point; configuration status and
watermark are unchanged.

### Disable

Atomically change configuration status to `disabled` first, preserving stream
identity and replay watermark. Then delete the sidecar and deallocate runtime.
An interrupted deletion leaves a removable orphan, while disabled configuration
remains authoritative.

### Accepted observation

An accepted observation changes both artifacts in this exact order:

1. atomically write the sidecar containing the new recursive state and new
   accepted sequence;
2. atomically advance the configuration watermark to that sequence; and
3. only then report success or invoke a projection/diagnostic sink.

If step 1 fails, configuration remains unchanged and the observation fails. If
step 1 succeeds but step 2 fails, do not reapply the observation or invoke the
sink; no new observation is admitted until recovery completes.

### Shutdown

Shutdown changes no lifecycle status and no replay watermark. For active state,
it makes one best-effort atomic sidecar flush. On failure, the prior valid
sidecar remains authoritative, the failure is recorded as Brainvision-local
durability failure, no altered retry is made, runtime tears down, and native
`Fabric.close()` continues. Suspended state follows its already committed
frozen-time lifecycle; disabled state has no sidecar flush.

### Recovery matrix

| Recovered artifacts | Required outcome |
| --- | --- |
| configuration absent, sidecar present | integrity failure; no mutation or admission |
| disabled configuration, sidecar present | delete orphan and remain disabled |
| active/suspended configuration, sidecar missing | hard fail; never silently initialize |
| sidecar sequence equals configuration sequence | normal continuation |
| sidecar sequence greater than configuration sequence | validate lineage and repair configuration watermark upward before admission |
| configuration sequence greater than sidecar sequence | hard fail |

Disable may delete a sidecar only after the configuration watermark is confirmed
at least equal to the sidecar watermark. No observation is admitted until the
applicable reconciliation succeeds.

---

## 13. Unknown-agent behavior and synchronization

Direct visual ingress must never create an ordinary TORMENT agent. It must:

1. validate identifiers without allocation;
2. perform a non-mutating identity existence check;
3. refuse immediately when absent; and
4. only for a known agent acquire or create the normal per-agent lock entry and
   revalidate Brainvision configuration/status under that lock.

Unknown ingress creates no lock registry entry, native state, private graph,
Brainvision state, or filesystem agent state. It never calls `create_agent` or
ordinary ingest.

Brainvision sidecar I/O uses only the lawful per-agent synchronization boundary.
It must not introduce a workspace-to-agent lock dependency or change native
shutdown failure semantics.

---

## 14. Anti-tuning, failure authority, and versioning

Phase 4 freezes equations, parameters, gate behavior, state representation,
and operator identity before Phase-6 acceptance. Phase 5 freezes projection
fields, relevant sets, normalization, and quantization before acceptance
results are inspected.

The retained-history target must differ by at least two canonical quantization
codes in at least one `RETAINED_HISTORY_ROLE` field, while current activity is
equal under its frozen role. This prevents an arbitrarily tiny bin-edge-only
success.

If baseline acceptance fails, return `VHE_ACCEPTANCE_FAIL`. The 300-second
product requirement remains fixed. Changing the operator requires a new
operator identity; changing projection or quantization requires a new
projection identity; all dependent validation is rerun. Projection resolution
cannot be reduced merely to rescue a failed horizon result without explicit
product-level reauthorization.

The same requalification discipline applies to changed modulation axes, domain,
mapping, effect criterion, or validation grid.

---

## 15. Phase order and exit criteria

The frozen implementation order is:

| Phase | Scope |
| --- | --- |
| 0 | specification |
| 1 | package shell |
| 2 | observation contract and canonical fixtures |
| 3 | visual clock |
| 4 | VHE/operator freeze |
| 5 | projection |
| 6 | baseline horizon validation |
| 7 | character modulation |
| 8 | configuration |
| 9 | sidecar |
| 10 | Fabric lifecycle |
| 11 | direct ingress |
| 12 | null/test sinks |
| 13 | v1a qualification |
| HOLD | no v1a-to-v1b expansion |
| 14+ | governed v1b integration |

Phase 0 freezes the product horizon, fixture roles, visual-time and replay
semantics, exact relations, isolation rules, lifecycle and persistence model,
recovery matrix, modulation contract, anti-tuning authority, unknown-agent
behavior, shutdown behavior, and redesign/revalidation boundary.

Phase 1 may begin only under separate authorization. This specification does
not itself authorize Phase 1 or any later phase.
