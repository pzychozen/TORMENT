# 7G5E4D-D1 shared M1 and shared-trigger mood drift

## Qualified boundary

D1 qualifies only this shared CREATED_NEW suffix:

~~~
shared native source already committed
  -> shared-domain M1 maintenance
  -> identity-anchor emission call       (D0 required no-op)
  -> identity-anchor refinement call     (D0 required no-op)
  -> mood drift -> private triggering-agent derived row, when the existing law emits
  -> return at the world-step boundary
~~~

The adapter invokes the existing LegacyFabricPostWriteAdapter
_run_motif_maintenance_and_anchors orchestration rather than copying its
algorithm. Its independent exception boundaries remain: M1 failure is caught
before both D0 anchor calls and mood drift; mood failure is caught before the
D1 branch returns. No later consumer is executed.

This is not direct shared ingest, a production backend selector/activation,
dual write/read, vector freshness, world/trajectory/SRG, Hivemind, Character,
checkpoint, compression, or a composition with B1.

The new profile is core_staging_with_shared_m1_mood_drift:

~~~
shared_motif_suggestion_maintenance = QUALIFIED
shared_trigger_identity_anchor      = REQUIRED_NOOP
shared_trigger_mood_drift           = QUALIFIED
~~~

It requires a claimed SHARED_DOMAIN source, an explicit admitted PRIVATE_AGENT
mood target, and rejects a source-scope derived template or B1 composition.

## Shared M1 and D0

M1 reads current native shared-domain motif geometry through
NativeScopedMotifGeometryAdapter and keeps the existing external workflow
store as owner. It passes the current domain-policy fields without translation:

- motif_entropy_target_n
- motif_entropy_high
- motif_merge_similarity
- motif_merge_max_suggestions
- auto_merge_motifs
- auto_merge_entropy_trigger

Suggestion-only M1 writes the existing motif_events.jsonl and motif_merges.json
workflow state; it never creates a legacy MotifRegistry or motifs.json. If
auto_merge_motifs is true, D1 supplies the already-qualified M2
NativeMotifMergeRuntime for the same claimed shared scope.

D0 remains a hard producer boundary. The anchor calls retain their position in
the sequence, but a shared trigger returns before scope checks, private reads,
embedding, source/member EID interpretation, native creation, lifecycle
publication, or anchors.json access. No shared-to-private EID mapping exists.

## Mood topology

Local legacy behavior consumes only the triggering agent's affect state, step,
affect tag/confidence, and domain label. It does not consume a shared motif
member EID or use a shared source object as a private parent. The D1 binding
therefore makes target scope explicit:

| Fact | D1 value |
| --- | --- |
| Trigger scope | shared (research in the qualification fixture) |
| Affect side-store owner | external affect_state.json for ws / aria |
| Derived target | admitted PRIVATE_AGENT ws / aria |
| Target identity, semantic, idempotency namespaces | the admitted private scope |
| Payload domain | the triggering shared domain, research |

NativeSharedTriggerMoodDriftBinding carries the target routing scope and its
derived-runtime template. The shared domain is a context/payload fact; it is
not used as the private target semantic scope.

The existing decision order is unchanged: absent/neutral affect, disabled
environment, and low confidence return first. Otherwise native loads affect
state, captures the prior tag/step, persists the latest affect best-effort,
then applies the original prior-non-neutral/tag-changed/minimum-gap law.

When emitted, the row preserves the existing summary, mood_drift/core/non-canon
facts, strength/confidence formula, configured half-life, attribution, and
embedding metadata. The covered sad -> angry shared-trigger transition creates
zero shared mood rows and one private ws / aria row. It has no source_eid,
source_member_eids, parent_eid, or other bare shared-to-private EID provenance.

~~~
SHARED_TRIGGER_MOOD_DRIFT_TARGET = PRIVATE_AGENT
SHARED_TO_PRIVATE_BARE_EID_PROVENANCE = NONE
PRIVATE_DERIVED_REPRESENTATION_BECAME_READY = YES
affected lane = ws / PRIVATE_AGENT aria / emitted private compatibility EID
~~~

The representation consequence is recorded only; D1 adds no vector
invalidation or refresh work.

## Side store and lost-response recovery

The initial affect save remains best-effort and occurs before native creation.
After successful creation, the runtime reloads the state, appends the bounded
50-entry drift history, and saves best-effort. SQLite and affect_state.json
remain non-atomic. D1 covers initial-save failure, memory-creation failure, and
history-save failure.

The pre-create save makes an exact retry after a lost response look like the
same affect tag. D1 adds a narrow recovery check only for an existing matching
private mood_drift source: same private workspace/agent lane, shared-domain
payload, destination tag, step, stored prior tag, stored creation timestamp,
and same derived child parent key. A later ordinary same-tag event uses a
different parent key and cannot become a duplicate.

NativeDerivedMemoryCreationService remains the only publisher. It recovers the
same source, PENDING, expectation, and READY operations. A changed retry
intent reaches the existing source and fails closed with
SubstrateIdempotencyConflict. Tests cover source, PENDING, and READY response
loss with one final usable READY representation and the same compatibility EID.

## Frozen shared-consumer matrix

The full legacy created-memory branch structurally orders contradiction, SRG,
Hivemind, then M1/derived; its all-outcomes suffix is world, Character,
checkpoint, compression, proposal, bridge. D1 intentionally enters only the
M1/derived suffix. The table records the whole shared topology.

| Consumer / full-legacy position | Shared gate, inputs, and observable effect | Failure topology | Classification / blocker |
| --- | --- | --- | --- |
| Contradiction, created #1 before M1 | Explicit private/core/EID gate; otherwise reads embeddings and writes external conflicts. | Caught, debug logged. | SHARED_NO_OP / no |
| SRG transient collision, created #2 before M1 | No scope gate; owner SRG enable + srg_state + EID. Enumerates current memory/embedding and applies current collision state. Native version is a namespaced process overlay, not an immediate SQLite write. | Caught, debug logged. | PROCESS_ONLY; not run by D1, later scope/order prerequisite |
| Hivemind packet/proposal, created #3 before M1 | No shared exclusion; enabled/stored/EID/packet gate. Reads memory, governance, Character state; may append collective packet, telemetry, and external proposal draft. | Inner failures caught; outer error logged with telemetry attempt. | ACTIVE_SHARED_EFFECT / BLOCKED |
| M1 + D0 anchors + mood, created #4 | D1 shared geometry/external workflow; anchors no-op; mood can write private derived row, READY representation, and affect state. | M1, anchor emit, anchor refine, mood separately fail-soft. | QUALIFIED / D1 endpoint |
| World step, after created branch | Every outcome; advances source-namespace physics. Every 50 steps adds process trajectory diagnostic overlay. | Caught, debug logged. | PROCESS_ONLY / BLOCKED |
| Trajectory diagnostic materialization, within world/later successor | Reads world histories; overlay may later become an authorized memory successor contribution, not an immediate post-write row. | World/successor boundary. | PROCESS_ONLY / BLOCKED; trajectory_evidence refused |
| Character measurement/state/gravity/reflex, after world | Owner enable/cadence; may read/save Character state, correct graph/motifs, and call reflex. No shared no-op gate. | Broadly caught. | ACTIVE_SHARED_EFFECT / BLOCKED |
| Checkpoint, after Character | Enable/interval gate; reads motif summary, private embedding shard, Character state; can write checkpoint files. | Nested/outer failures debug logged. | ACTIVE_SHARED_EFFECT / BLOCKED |
| Compression/deep memory, after checkpoint | Owner enable/min-step; can compress and export deep state. No shared no-op gate. | Broadly caught. | ACTIVE_SHARED_EFFECT / BLOCKED |
| Proposal orchestration, after compression | Explicit context.scope == private plus stored/coupling/half-life/policy gates. | Gated return; registry errors propagate. | SHARED_NO_OP / no |
| B1 bridge, final | Stored + random gate; reads supplied multi-domain geometry and can write bridge workflow. | Deliberately fail-loud. | ALREADY_QUALIFIED only as separate B1 capability; D1 composition refused |

~~~
POST_D1_SHARED_CONSUMER_MATRIX = FROZEN
UNRELATED_SHARED_POST_WRITE_CAPABILITIES = STILL_REFUSED
~~~

## Evidence and retained posture

tests/test_substrate_native_shared_m1_mood_post_write.py covers exact
M1 -> anchor no-op -> refine no-op -> mood order; no-mood and mood cases; M2
reuse; M1/mood failure topology; all three affect side-store failures; and
source/PENDING/READY recovery with changed-intent refusal. It proves private
target placement, zero shared mood rows, no bare-EID payload provenance, and
no shadow legacy motif state.

~~~
SHARED_M1_POST_WRITE = QUALIFIED
SHARED_M1_FAILURE_TOPOLOGY_PARITY = PASS
D0_SHARED_ANCHOR_SCOPE_ISOLATION_REGRESSION = PASS
SHARED_D1_CALL_ORDER_PARITY = PASS
SHARED_TRIGGER_MOOD_DRIFT_DECISION_PARITY = PASS
SHARED_TRIGGER_MOOD_DRIFT_STORAGE_PARITY = PASS
SHARED_TRIGGER_AFFECT_SIDE_STORE_PARITY = PASS
SHARED_MOOD_FAILURE_TOPOLOGY_PARITY = PASS
SHARED_TRIGGER_MOOD_LOST_RESPONSE_RECOVERY = PASS
POST_D1_SHARED_CONSUMER_MATRIX = FROZEN
SHADOW_LEGACY_MEMORY_STATE = NONE
SHADOW_LEGACY_MOTIF_STATE = NONE
KERNEL_FILES_CHANGED = 0
PUBLIC_INGEST_BACKEND = LEGACY
PRODUCTION_SELECTOR_ADDED = NO
NATIVE_ACTIVE = NO
DUAL_WRITE = NO
DUAL_READ = NO
CUTOVER_OPENED = NO
~~~

Native qualification used conda environment torment-substrate with SQLite
3.53.4. The ordinary torment environment remains unchanged.
