# 7G5E4D-D2 remaining shared post-write consumer disposition

## Scope and frozen boundary

D2 begins from `ac294b9 Qualify 7G5E4D shared M1 mood post-write`.
It traces the actual legacy `CREATED_NEW` shared-ingest path before selecting
one additional consumer. No public Fabric selector, activation, dual
write/read, cutover, vector invalidation, kernel change, or broad shared
post-write profile is introduced.

The legacy order is:

~~~text
created only:
  contradiction -> SRG -> Hivemind -> M1/D0/mood
all outcomes:
  world -> Character -> checkpoint -> compression -> proposal -> B1 bridge
~~~

For legacy shared ingest, Fabric selects `workspace.shared_graphs[domain]`
before memory creation. The newly created shared source is spawned into that
graph's world and enters its shared-domain world topology. D1's mood-derived
row is different: it is registered independently in the triggering agent's
private native world lane only when the mood law emits it. A shared trigger
therefore does not imply a shared target.

## D2 qualified Hivemind boundary

Hivemind was the earliest real unqualified created-memory effect (position
three, before M1). D2 qualifies it as a separate, non-composed shared profile:

~~~text
current claimed SHARED_DOMAIN native source
  -> namespace-scoped NativePostWriteMemoryAccess current read
  -> existing TORMENT CollectiveField.append_packet
  -> existing TORMENT telemetry and CollectiveProposalBridge, if converged
  -> return
~~~

The profile is
`core_staging_with_shared_hivemind_packet_emission`. It requires an explicit
shared Hivemind flag and refuses composition with D1 M1/mood or B1 bridge
profiles. It runs only for a current `CREATED_NEW` route witness.

The legacy predicate is unchanged:

- Hivemind must be enabled; the context must be stored, have an EID, and not
  request `skip_packet_emission`.
- The current source governance must permit collective export and it must not
  be a collective echo.
- Coherence must be at least `0.15` to append a packet. Telemetry may record a
  skipped outcome otherwise.
- A returned convergence is handed to the existing proposal bridge with the
  existing external domain proposal registry. SQLite does not create a packet,
  convergence, or proposal.

`ResonancePacket` carries a bare `source_eid`, and a convergence event contains
a list of bare EIDs. That is retained external provenance only: the collective
field and `reingest_convergence` use packet/event/domain/agent data and do not
resolve those values into a private or shared memory graph. The D2 binding
reads the source only through the claimed shared legacy-source namespace, so it
does not create a shared-to-private EID mapping. Repeated post-write calls keep
legacy behavior: SQLite creates no extra row and the external collective owner
receives the repeat, where its own persistence/deduplication policy remains
authoritative. Packet and proposal-bridge failures remain fail-soft; the
existing telemetry error attempt is retained.

## Verified shared consumer matrix

| Consumer | Classification | Trigger | Target/owner | Durable effect? | Native status | Next action |
| --- | --- | --- | --- | --- | --- | --- |
| Contradiction surface | SHARED_NO_OP | Created shared source reaches the first call site. | None: predicate requires `scope == private`, core, EID. | No. | No native work needed. | Preserve the predicate. |
| SRG transient collision | PROCESS_ONLY | Created shared source when SRG is enabled, `srg_state` exists, and EID exists. | Reads the selected shared graph/source and shared embeddings; writes a process SRG overlay keyed by core, source namespace, and EID. | No immediate durable write; a later separately authorized successor may materialize an overlay. | `NativeSRGTransientRuntime` has the equivalent namespace-scoped overlay; D2 Hivemind does not need to invoke it. | Keep SRG mathematics and successor materialization out of D2. |
| Hivemind packet / convergence / proposal delegation | ALREADY_QUALIFIED | Created shared source; enabled/stored/EID/no-skip, export allowed, coherence >= 0.15. | Existing external CollectiveField, telemetry sink, and CollectiveProposalBridge; source facts come from the claimed shared namespace. | Yes, external packet/event/tracker/proposal-workflow effects; no SQLite authority. | Qualified by D2's separate shared Hivemind profile. | Do not compose it yet with D1/B1 or move external ownership. |
| M1 suggestion / M2 merge / D0 anchors / mood | ALREADY_QUALIFIED | Created shared source after Hivemind. | M1/M2 workflow is external shared-domain state; D0 anchors are required no-ops; mood target is the triggering agent's private lane and affect store. | M1/M2 workflow and optional private mood source/READY representation. | Qualified by D1/M2. | Retain the D1 separate profile. |
| World physics step | PROCESS_ONLY | Every stored outcome, including shared `CREATED_NEW`, through the selected shared graph. | The shared source and all selected shared graph entities enter/advance in a process-owned shared-domain world. Private mood enters a separate private world only if D1 emitted it. | Physics state itself is process-local. | `NativeWorldRuntime` already provides namespace-scoped initialization, fresh registration, and process advance. | Do not compose/activate it here; trajectory evidence is separately blocked. |
| World / trajectory diagnostics | BLOCKED | Every world step writes a trajectory frame (`log_every=1`); genesis entries are also written as needed. Every 50 steps it adds RAM labels and a legacy memory-events diagnostic. | Selected shared graph's external Trajectory V2 writer (or legacy trajectory writer); not a private mood lane. | Yes: external genesis, chunk/frame, boundary/diagnostic artifacts. The classify payload overlay itself is RAM until a later legacy successor. | Native world has only process overlay and successor preparation; no qualified trajectory writer/evidence owner. | Next durable blocker after D2; qualify only with exact external evidence ownership and recovery policy. |
| Character measurement | BLOCKED | Stored, positive step divisible by Character cadence, and only `CREATED_NEW` measures. | Reads the selected shared graph and selected shared-domain motif registry, plus an external agent Character seed/state. | Measurement feeds external state; no source row is created by measurement alone. | Native measurement can read a scoped namespace but no shared post-write profile binds it. | Treat shared source facts and private Character owner as an explicit future slice. |
| Character state / gravity / reflex / seed | BLOCKED | Measurement result; high drift requires away-seed threshold. | CharacterState and seed remain external per workspace/agent. Legacy gravity receives the selected shared graph and may create a shared `drift_correction` row/motif; reflex is an external callback. | Yes: CharacterState; possibly shared correction memory/representation; callback side effect. | Native gravity exists but is not bound to this mixed shared-source/private-state topology. | Freeze as a later Character slice; do not infer a private correction target from the triggering agent. |
| Checkpoint | BLOCKED | Every stored outcome only when checkpoint is enabled, step is positive, and step reaches its interval. | External checkpoint owner reads shared-domain motif summary, the triggering agent's private embedding-shard snapshot, external CharacterState, and per-agent kernel context. | Yes, external recovery/checkpoint files; they are not new SQLite memory truth. | No shared checkpoint binding; native adapter deliberately forbids it. | Preserve external owner and define recovery semantics separately. |
| Compression / deep memory | BLOCKED | Every post-write reaches it; enabled and `step >= compress_min_step` gates actual work. | The trigger is shared, but both `try_compress` and hard-cap lookup use only `private_graphs[workspace, agent]` and that agent's external deep store. | Potentially yes: private graph payload updates plus external deep export/index/log. It never consumes the shared source EID. | Native profile refuses compression/deep memory. | Later private-lane compression slice. No bare shared-to-private EID mapping was found. |
| Ordinary proposal orchestration | SHARED_NO_OP | Every post-write reaches it. | None: predicate explicitly requires private scope plus coupling/policy gates. | No. | No native work needed. | Preserve the scope gate. |
| B1 bridge suggestions | ALREADY_QUALIFIED | Final post-write slot when stored and its existing random gate allows it. | Existing external BridgeRegistry with qualified read-only native multi-domain geometry. | External bridge workflow only. | B1 separate qualified profile remains callable for a direct shared route. | Regressed in D2; no composition with D2 Hivemind. |

Failure topology is retained per row: SRG and world are caught/debug logged;
Hivemind has its existing inner best-effort reads and outer fail-soft telemetry
attempt; Character and compression are broadly fail-soft; checkpoint has nested
best-effort reads plus an outer debug failure; proposal is a gated return; and
B1 deliberately remains fail-loud. The D2 adapter itself only calls the
Hivemind consumer, so excluded consumers are represented by forbidden
dependencies rather than accidental legacy `MemoryGraph` access.

## Affected vector lanes by effect

| Effect | Source/target lane | Representation consequence | D2 disposition |
| --- | --- | --- | --- |
| Direct shared original | Shared domain | The routed source has its native READY representation in the shared-domain compatibility lane. | Existing route behavior; no invalidation added. |
| D1 mood drift, when emitted | Private agent lane of the triggering agent | One private derived source with a READY representation. | D1-qualified; no invalidation added. |
| Hivemind packet / proposal | No new memory lane | Uses the existing source vector for in-process similarity; JSONL packet stores a hash, not a new native representation. | D2-qualified external effect only. |
| Character gravity, if later due/high drift | Shared domain in legacy behavior | A legacy `drift_correction` would be born in the selected shared graph and receive a shared vector. | Blocked; record for final freshness work. |
| Compression/deep export, if later triggered | Existing private agent source to external deep lane | Reads private source embeddings and can export deep-memory payload/vector state; no shared source EID is used. | Blocked; external/private-lane work. |

~~~text
AFFECTED_VECTOR_LANES_BY_EFFECT = FROZEN
shared original -> shared-domain native vector lane
shared trigger mood -> triggering-agent private native vector lane (conditional)
Hivemind -> no new native lane
future Character gravity -> shared-domain lane (conditional, blocked)
future compression/deep -> private external deep lane (conditional, blocked)
~~~

## Evidence and final D2 posture

`tests/test_substrate_native_shared_m1_mood_post_write.py` now proves D2's
current shared-source native read, external packet/telemetry/proposal
delegation, retry posture without native row creation, fail-soft external field
failure, and D1/D2 composition refusal. The wider post-write suite retains
legacy order, D0 no-op, D1 mood, M1/M2, B1, and remaining consumer gates.

~~~text
POST_D1_SHARED_CONSUMER_MATRIX = VERIFIED
WORLD_SHARED_DISPOSITION = FROZEN
SRG_SHARED_DISPOSITION = FROZEN
HIVEMIND_SHARED_DISPOSITION = QUALIFIED
CHARACTER_SHARED_DISPOSITION = FROZEN
CHECKPOINT_SHARED_DISPOSITION = FROZEN
COMPRESSION_SHARED_DISPOSITION = FROZEN
B1_SHARED_BRIDGE_REGRESSION = PASS
AFFECTED_VECTOR_LANES_BY_EFFECT = FROZEN

KERNEL_FILES_CHANGED = 0
PUBLIC_INGEST_BACKEND = LEGACY
PRODUCTION_SELECTOR_ADDED = NO
NATIVE_ACTIVE = NO
DUAL_WRITE = NO
DUAL_READ = NO
CUTOVER_OPENED = NO
~~~

The next earliest remaining durable consumer is trajectory evidence, after the
now-qualified Hivemind and D1 suffix. It is intentionally not implemented in
D2.
