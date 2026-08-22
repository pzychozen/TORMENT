# TORMENT Brainvision — Phase 12 Null/Test Sink Specification v1.0

## Status and authority

**FROZEN PRE-IMPLEMENTATION PHASE-12 SPECIFICATION — DOCUMENTATION ONLY**

Phase 12 defines a bounded Brainvision-owned diagnostic sink boundary for the exact canonical projection of a successfully committed `FIRSTHAND_VISUAL` observation. It is compatible with frozen and accepted Phases 0–11, does not reopen them, and does not authorize ordinary Fabric ingest, cognition, memory, kernel, prompt/model, SRG, Hivermind, or Spine integration.

Authoritative pre-Phase-12 baseline:

```text
c017df35158e5cce6b6d5d328f57bccab2e1f278
```

## 1. Ownership and path

Phase 12 owns optional diagnostic sink hosting, exact commit-time projection capture, passive delivery, same-agent delivery ordering, process-local diagnostics, test-only passive recording support, and boundary tests. It does not reinterpret or grade projections.

Phase 11 continues to own the typed observation boundary, lineage/replay/identity admission, successor derivation, Phase-10 transaction delegation, and unchanged receipt. Phase 10 continues to own known-agent proof, the per-agent `RLock`, clock, recovery, persistence order, runtime adoption, and committed snapshot creation. Phase 5 continues to own all projection mathematics and identities.

```text
FIRSTHAND_VISUAL -> bound Phase-12 host -> Phase-11 ingress
-> Phase-10 transaction -> Phase-7/4 update -> durable commit
-> committed snapshot -> Phase-5 projection elapsed=0 -> detached mapping
-> release agent lock -> optional sink -> unchanged Phase-11 receipt
```

No Phase-12 output may enter ordinary TORMENT cognition or memory systems.

## 2. Frozen commit-time projection

Phase 12 supports exactly one projection timing: the accepted observation's exact committed successor state at its exact committed active time. It provides no sink-controlled as-of time, pull/query API, deferred or batched projection, arbitrary later read, or caller-selected elapsed interval.

The committed Phase-10 runtime snapshot contains `configuration`, `vhe_state`, and `active_time_ns`, after sidecar write, configuration-watermark write, and runtime adoption. The exact Phase-12 projection is:

```python
project_vhe_state(committed_snapshot.vhe_state, 0).to_dict()
```

Zero is mandatory: the snapshot already represents the committed active time. No further free evolution, clock sample, lifecycle read, or sidecar/configuration reread is lawful.

The detached payload contains exactly:

```text
schema_id
projection_id
operator_id
current_activity_code
retained_history_code
present_history_relation_code
trajectory_code
open_event_class
recurrence_code
```

It contains no raw VHE/runtime handle and no Phase-12-added field.

## 3. Bound host, uniqueness, and registration

The host is conceptually:

```python
Phase12IngressHost(*, lifecycle_manager, workspace_id, agent_id, sink=None)
```

It is bound to one lifecycle manager, workspace ID, agent ID, and optional sink, and cannot admit another agent. For v1a there may be at most one live host for a given:

```text
(lifecycle_manager identity, workspace_id, agent_id)
```

A duplicate live host for that lineage must be refused at construction. The uniqueness registry and delivery-order gate are process-local only and are not configuration, sidecar state, VHE state, lifecycle state, or continuation identity. Host teardown or close releases the uniqueness claim. No global fan-out or shared multi-host delivery scheme exists in v1a.

Sink registration is process-local diagnostic apparatus. It must not enter configuration, sidecar, continuation identity, stream lineage, operator/projection/modulation identity, or the receipt. No sink identity is persisted.

## 4. Null behavior and sink protocol

The null sink is `None`; no `NullSink` object exists. With `sink=None`, the host delegates directly to accepted Phase-11 ingress, constructs no projection for delivery, invokes no callback, changes no Phase-12 counter, and returns the unchanged receipt.

The optional sink has one operation only:

```python
sink.on_projection(receipt, projection_payload) -> None
```

The return value is ignored. There are no lifecycle, rejection, state, recovery, query, or registration-mutation callbacks, and no fan-out.

Before the host becomes usable, a non-null sink must expose a callable `on_projection`. Missing or non-callable members refuse construction before ingress, transaction, VHE update, or durable commit. This is not projection-construction failure, delivery failure, or ingress failure.

## 5. Same-process delivery and agent-lock rule

Delivery occurs only after a successful committed `FIRSTHAND_VISUAL` observation. There is no delivery for enable, suspend, resume, reset, disable, configuration changes, recovery-only repair, rejection, failed observation, or pure projection read.

For each successful observation commit that reaches the live same-process Phase-12 post-commit path with a registered sink and successful projection construction, exactly one sink delivery attempt occurs.

A process interruption after durable commit but before projection construction or sink invocation may yield zero deliveries. Phase 12 has no persisted sink queue, recovery backfill, sink retry, delivery replay, sink-event reconstruction, or replay-bypass path. Recovery restores Brainvision continuation state only; it must not synthesize a missed sink event. Resubmission remains governed by normal Phase-11 replay refusal.

Within one live process and one live bound host, delivery order follows successful same-agent commit order. This is not a cross-process, persisted, or post-recovery callback-order guarantee; a crash may truncate delivered records while durable state contains additional accepted observations.

The process-local delivery-order gate is acquired before forwarding admission and remains held through the delivery attempt. It prevents N/N+1 reordering without altering recursive, lifecycle, configuration, sidecar, or identity state.

Projection data is fixed while the Phase-10 transaction protects correspondence, but arbitrary sink code executes only after the Phase-10 agent `RLock` is released:

```text
acquire Phase-12 gate -> enter Phase-11/10 transaction -> commit
-> obtain snapshot -> construct zero-elapsed payload -> release agent lock
-> invoke sink -> release gate -> return receipt
```

```text
PROJECTION_FIXED_UNDER_AGENT_LOCK = YES
SINK_EXECUTES_UNDER_AGENT_LOCK = NO
```

## 6. Internal seam, recorder, and prohibited data

Phase 12 may add a private internal capture seam in `brainvision/ingress.py` for the `BrainvisionRuntimeSnapshot` returned by `commit_successor()`. It must leave the public Phase-11 API, receipt, admission order, failure behavior, and null behavior unchanged. It exposes no raw-state API; the snapshot is available only to Brainvision-owned Phase-12 hosting code.

The recording sink is test/qualification support only and lives in `tests/` or equivalent non-production support. It is in-memory, append-only, ordered, passive, and non-persistent. It records only `(receipt, projection_payload)` and performs no acceptance grading or fixture comparison.

The sink must never expose raw VHE/Fast Trace/Persistent Context/Semantic Register data; `write_gate_q`, orientation, normalization, trace, or gain intermediates; theta, modulation details, frames, pixels, descriptors, fixtures, adapter-private data, timing internals, or MemoryGraph, kernel, CharacterSeed/State, CognitiveCore, SRG, Hivermind, Spine, prompts, model data, or LLM output.

## 7. Failure and metrics

If projection construction raises after commit, the observation remains committed, the receipt returns unchanged, the sink is not called, no retry occurs, and `projection_construction_failures_total` increments. It must not roll back state, reduce replay state, rerun VHE, or turn the commit into an ingress refusal.

If sink delivery raises, the observation remains committed, the receipt returns unchanged, no retry occurs, and `sink_delivery_failures_total` increments. Callback failure is not an ingress failure. Normal callback return increments `sink_invocations_total`; callback return data is ignored.

The only metrics are:

```text
sink_invocations_total
sink_delivery_failures_total
projection_construction_failures_total
```

They are host-owned, per-bound-host, process-local, non-persistent, and excluded from configuration, sidecar, receipt, projection, recursive state, and continuation identity. Phase 13 may read an immutable diagnostic snapshot.

## 8. Purity, scheduling, and determinism

Projection construction and delivery do not mutate F, S, R, VHE state, replay admission/watermark, configuration, sidecar content, future VHE mathematics, receipt, projection, or continuation identity. Under the same deterministic observation and clock schedule, sink absence, success, or failure yields identical committed artifacts and future controlled projections. Repeated hypothetical delivery of a detached payload cannot mutate the engine; production makes at most one live-process attempt.

Phase 12 samples no Brainvision monotonic clock for projection. It makes no claim that a slow synchronous sink cannot delay an external caller's later observation submission; that delay may affect the later active-time interval without being a direct sink mutation. Deterministic comparisons use controlled/injectable clocks.

For equivalent fresh processes and identical controlled observation, lifecycle, configuration, and clock schedules, receipts compare by exact equality of:

```text
observation_id
source_sequence
committed_active_time_ns
```

Projection determinism is established only through frozen Phase-5 canonical serialization:

```python
projection_a.to_canonical_json_bytes() == projection_b.to_canonical_json_bytes()
```

For sink-stored detached mappings, frozen Phase-5 serialization must yield byte-identical canonical projection bytes. Plain Python mapping equality is not normative. Phase 12 creates no serialization identity.

## 9. Multi-agent, persistence, and query limits

Process-global sink slots and lifecycle-manager-global unscoped sink slots are prohibited. Separate agent lineages use separate bound hosts and separate sink apparatus. Agent identifiers are not added to the receipt or payload.

Phase 12 persists no sink output: no JSON/JSONL, database rows, sidecar/configuration records, or authoritative qualification logs. It exposes no `get_projection_now()`, `read_projection()`, `project_as_of(...)`, `sink_query(...)`, or `state_snapshot(...)` API. The sink is push-only and observation-commit-bound.

## 10. Claim and Phase-13 entry boundaries

Phase-12 success establishes only exact commit-time canonical projection capture, correspondence to committed state/time, direct sink purity, deterministic controlled records, and ordinary-system isolation. It does not establish emotion, attention, awareness, consciousness, experience, semantic understanding, memory formation/duration, physical visual accuracy, model usefulness, or cognitive usefulness. Projection remains a lossy bounded relational encoding; insufficient Phase-13 evidence requires governed projection redesign, not hidden raw-state delivery.

For frozen `d0 = (500000, 0)`, normalization is `(0, 0)`. On the retained-history qualification fixture with `semantic_event_class=None`, the later lawful d0 observation has `write_gate_q=0`, makes no Persistent Context write, and makes no Semantic Register update. At the 300-active-second sampling point its prior Fast Trace has expired. This is a fixture-limited Phase-13 entry condition, not a universal d0 no-change claim.

## 11. Implementation scope and stop conditions

Expected scope:

```text
new: brainvision/sink.py
new: tests/test_brainvision_phase12_sink.py
test-only: passive recording sink/helper
narrow additive internal edit: brainvision/ingress.py
```

Phase 10 and Phase 11 require no semantic change. Implementation stops for architecture review if it requires public Phase-11 or Phase-10 semantic change, raw VHE exposure, configuration/sidecar/receipt/projection schema change, agent IDs in payload, ordinary Fabric integration, ordinary memory/kernel/cognition/model integration, persisted sink output, or a query/read API.

## 12. Required test matrix

The bounded suite contains 84 checks:

1–6 Null path: None host, unchanged receipt, no construction/callback, zero counters, and direct-Phase-11 byte/state equivalence.

7–12 Success: one record, receipt pairing, zero-elapsed committed-snapshot projection, nine fields, fresh detached mapping, and mutation isolation.

13–18 Concurrency: payload fixed before agent-lock release, callback after release, paused N delivery, N+1 attempt, N-before-N+1 record order, and frozen N payload.

19–21 Rejections: each stream, contract, replay, identity, inactive, and recovery refusal performs no construction, callback, or success-count change.

22–28 Construction failure: injected post-commit construction error, durable acceptance and receipt preserved, no call/retry, construction count one, delivery-failure count unchanged.

29–35 Delivery failure: throwing sink, durable acceptance and receipt preserved, one call/no retry, delivery-failure count one, construction count unchanged.

36–40 Purity: sink absent/success/failure produces equal sidecar, normal-watermark-equivalent configuration, equal successor/future controlled projection, and no payload feedback.

41–43 Determinism: repeated controlled schedule, exact receipt-triple sequence, and byte-identical Phase-5 canonical projection bytes.

44–47 Multi-agent: separate A/B hosts and sinks, no cross-delivery, no payload identifier widening.

48–53 Lifecycle exclusion: no record for enable, suspend, resume, reset, disable, or recovery-only repair.

54–57 Metrics: immutable, process-local, non-persistent, and identity/receipt/projection-independent.

58–69 Static isolation: no Fabric ingest, memory, kernel, CharacterSeed/State, cognition, SRG, Hivermind, Spine, prompt/model/LLM, persisted output, query API, or raw-state sink surface.

70–79 Host validation/uniqueness: missing member refused, non-callable member refused, callable and None accepted, first host succeeds, duplicate same-lineage host refused, different agent succeeds, manager-instance identity is exact, replacement after release succeeds, and duplicate refusal creates no Brainvision artifact or VHE mutation.

80–84 Crash window: characterize durable commit followed by test-only/narrowly-internal post-commit/pre-delivery interruption; acceptance remains durable, recovery has no backfill, same sequence is replay-refused, and VHE is not duplicated. The seam never becomes a production recovery-delivery feature.

## 13. Regression, phase boundary, and freeze

Implementation acceptance runs Phase-12 focused tests, full Brainvision regression, Phase-11 focused regression, Phase-10 lifecycle/recovery regression, relevant Fabric/path-security regression, `py_compile`, and `git diff --check`. Earlier scientific acceptance tests invoked by regression remain `REPRODUCTION / REGRESSION ONLY`; no new Phase-6 or Phase-7 administration occurs.

Successful Phase-12 completion authorizes only Phase 13 — complete v1a qualification. A mandatory hold follows Phase 13; governed v1b work needs explicit later authorization.

Required pre-freeze review result:

```text
PHASE_12_SPECIFICATION_REVIEW:
PASS
```

Only then may this status change from `PRE-FREEZE CANDIDATE` to `FROZEN PRE-IMPLEMENTATION PHASE-12 SPECIFICATION`. Implementation begins from the exact commit containing the frozen specification.
