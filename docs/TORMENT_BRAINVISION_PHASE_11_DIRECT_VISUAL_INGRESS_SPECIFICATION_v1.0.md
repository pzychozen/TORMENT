# TORMENT Brainvision — Phase 11 Direct Visual Ingress Specification v1.0

## Status and authority

**PRE-FREEZE CANDIDATE — DOCUMENTATION ONLY**

This document defines the Phase-11 direct `FIRSTHAND_VISUAL` ingress contract for TORMENT Brainvision v1a.

It is derived from and must remain compatible with the frozen requirements of:

* Phase 0 — Production Specification
* Phase 2 — Observation Contract
* Phase 4 — Fixed-Point VHE Operator
* Phase 7 — `CONTEXT_INTEGRATION` Character Modulation
* Phase 8 — Configuration
* Phase 9 — VHE Sidecar Persistence
* Phase 10 — Fabric Lifecycle / Recovery Hosting

Phase 11 does not reopen those phases.

This specification authorizes no ordinary TORMENT ingest integration, no cognitive integration, no memory integration, no kernel integration, no model integration, and no Phase-12 sink.

The Phase-11 purpose is limited to:

> Admit exactly one already-validated typed `FIRSTHAND_VISUAL` observation into one active Brainvision configuration lineage, derive exactly one successor VHE state using the frozen Phase-4/7 mathematics, and commit it through the Phase-10 transaction boundary.

Authoritative repository at specification time:

```text
C:\TORMENT\TORMENT_repo\TORMENT-fabric_v2\torment_fabric
```

Authoritative pre-Phase-11 implementation baseline:

```text
329b4b26376f3415e145e75298c6a8d7843827de
```

---

## 1. Phase ownership

### Phase 11 owns

Phase 11 owns only:

1. The direct typed visual-ingress API.
2. Exact typed-observation boundary enforcement.
3. Stream-identity admission.
4. Adapter-contract admission.
5. Replay/high-water admission.
6. Canonical observation-identity verification at the ingress boundary.
7. Invocation of the frozen Phase-7/4 VHE successor operator.
8. Verification that the derived successor corresponds to the Phase-10 active-time cutoff.
9. Delegation of durable observation commit to Phase 10.
10. A minimal post-commit acceptance receipt.

### Phase 10 continues to own

Phase 10 remains authoritative for:

1. Known-agent proof.
2. Proof-before-lock-allocation behavior.
3. Agent-lock allocation.
4. Same-agent `RLock` serialization.
5. Lazy recovery.
6. Active/suspended/disabled lifecycle state.
7. Runtime construction and deallocation.
8. Active visual clock staging.
9. Sidecar/configuration compatibility.
10. Sidecar-first/configuration-second durable observation commit.
11. Runtime adoption only after durable commit.
12. Runtime drop after partial durable commit.
13. `SIDECAR_AHEAD` repair.
14. Shutdown resolution.
15. Recovery/integrity failures.

Phase 11 must not duplicate those responsibilities.

### Earlier phases continue to own

Phase 2 owns the observation DTO and deterministic observation-ID format.

Phase 4 owns baseline VHE mathematics.

Phase 7 owns the frozen Brainvision-specific `CONTEXT_INTEGRATION` modulation mapping.

Phase 8 owns configuration representation and exact configuration persistence primitives.

Phase 9 owns sidecar representation and exact continuation-state persistence.

---

## 2. Architectural boundary

The canonical v1a ingress path is:

```text
upstream visual adapter
        |
        v
FirsthandVisualObservationV1
        |
        v
Phase-11 direct admission
        |
        v
Phase-10 active_transaction(...)
        |
        v
Phase-7 / Phase-4 successor update
        |
        v
Phase-10 commit_successor(...)
        |
        v
minimal Phase-11 acceptance receipt
```

The direct ingress path is Brainvision-owned.

It is not ordinary TORMENT ingest.

Phase 11 must not route the observation through:

```text
Fabric.ingest
MemoryGraph
memory formation
memory retrieval
TriOcta/native memory kernel
CharacterSeed
CharacterState
SRG
Hivermind
CognitiveCore
prompt construction
model inference
LLM inference
Spine
```

No Phase-11 implementation may create a hidden alternate route into any of those systems.

---

## 3. API boundary

The preferred Phase-11 implementation location is:

```text
brainvision/ingress.py
```

The direct ingress API is conceptually:

```python
def admit_firsthand_visual_observation(
    *,
    lifecycle_manager: BrainvisionLifecycleManager,
    workspace_id: str,
    agent_id: str,
    observation: FirsthandVisualObservationV1,
) -> FirsthandVisualAdmissionReceipt:
    ...
```

The exact public symbol names may be finalized during bounded implementation only if semantics remain identical.

Phase 11 must remain independent of `torment_service.fabric`.

Phase 11 must not add:

* a `TormentFabric.ingest` branch;
* a general TORMENT ingress route;
* a Brainvision HTTP/API route;
* a sink;
* a model consumer;
* a memory consumer.

A later explicitly governed hosting surface may call this Brainvision-owned ingress function, but that is not part of Phase 11 unless separately authorized.

---

## 4. Exact observation type boundary

Phase 11 accepts only:

```python
type(observation) is FirsthandVisualObservationV1
```

Subclass acceptance is not required.

Raw mappings are not accepted.

Raw JSON is not accepted.

Phase 11 does not provide a second observation parser.

Phase 11 does not provide a second observation DTO.

Phase 11 does not coerce malformed observations into valid observations.

The Phase-2 observation type remains the sole typed `FIRSTHAND_VISUAL` observation contract.

An invalid object supplied at the Phase-11 API boundary produces a Phase-11 malformed-observation failure before VHE successor derivation or commit.

---

## 5. Phase-2 observation invariants retained

The accepted observation must already satisfy the frozen Phase-2 contract, including:

```text
schema_id =
brainvision.firsthand_visual_observation.v1

provenance_type =
FIRSTHAND_VISUAL
```

The observation envelope contains exactly the Phase-2-defined fields.

No Phase-11 field is added to the observation.

The adapter may not provide:

* Brainvision visual time;
* lifecycle status;
* replay watermark;
* VHE state;
* projection state;
* acceptance state;
* commit state.

Those remain Brainvision-owned.

---

## 6. Configured lineage binding

Each Phase-11 observation is admitted against one already-existing Brainvision configuration lineage.

The observation's:

```text
stream_identity
```

must equal the configuration's:

```text
stream_identity
```

exactly.

The observation's:

```text
adapter_contract_id
```

must equal the configuration's:

```text
adapter_contract_id
```

exactly.

No aliasing, normalization, rebinding, case folding, fallback, or compatibility conversion is allowed.

A different stream or measurement contract requires a different Brainvision configuration lineage under the previously frozen lifecycle rules.

---

## 7. Exact admission ordering

After Phase 11 enters the Phase-10 active transaction, admission checks occur in this exact order:

```text
1. stream_identity match
2. adapter_contract_id match
3. replay/high-water check
4. canonical observation_id verification
5. successor-state derivation
6. Phase-10 durable commit
7. acceptance receipt
```

This order is normative.

It must not be reordered merely for convenience.

---

## 8. Active-transaction requirement

Phase 11 must perform lineage-sensitive admission inside:

```python
BrainvisionLifecycleManager.active_transaction(...)
```

The transaction remains open and the same-agent lock remains held through:

* stream admission;
* adapter-contract admission;
* replay admission;
* observation-ID verification;
* successor derivation;
* durable commit.

Phase 11 must not perform a check-then-lock sequence that allows lifecycle or watermark state to change between admission and commit.

The transaction supplies the authoritative in-lock values required by Phase 11.

---

## 9. Known-agent and lifecycle behavior

Phase 11 does not perform an independent known-agent test.

It relies on the Phase-10 active-transaction boundary.

Therefore the already-frozen Phase-10 behavior remains authoritative:

* unknown agent creates no Brainvision artifact;
* known-agent proof occurs before lock allocation;
* agent identity is revalidated under lock;
* active Brainvision is required for observation mutation;
* suspended Brainvision refuses observation mutation;
* disabled Brainvision refuses observation mutation;
* absent configuration does not create a configuration;
* missing or incompatible required continuation state is a hard failure.

Phase 11 must not automatically enable Brainvision.

Phase 11 must not create configuration.

Phase 11 must not repair lifecycle state independently.

---

## 10. Replay/high-water admission

The authoritative durable replay lineage is represented by:

```text
configuration.last_accepted_source_sequence
```

Phase 10 exposes the lawful transaction replay watermark to Phase 11.

The frozen Phase-11 replay rule is:

```text
if observation.source_sequence
   <= transaction.current_replay_watermark:

    REFUSED_REPLAY
```

A replay refusal occurs before observation-ID verification for that stale sequence.

No VHE operator is invoked.

No durable artifact changes.

No runtime state changes.

No sink is invoked.

No receipt is returned.

Sequence gaps are valid.

Phase 11 must not require:

```text
source_sequence == watermark + 1
```

Only strict greater-than admission is required:

```text
source_sequence > watermark
```

---

## 11. Replay precedence over observation-ID validity

Replay precedence is intentional and frozen.

For example, if the durable watermark is:

```text
7
```

and an incoming observation has:

```text
source_sequence = 7
```

then the outcome is:

```text
REFUSED_REPLAY
```

even if its supplied `observation_id` is forged or noncanonical.

Phase 11 must not return `INVALID_OBSERVATION_ID` first for an already-replayed sequence.

This preserves the frozen Phase-0 replay semantics.

---

## 12. Observation identity verification

For a source sequence strictly above the replay watermark, Phase 11 verifies the exact Phase-2 canonical observation identity.

The identity binds exactly:

```text
(stream_identity, source_sequence)
```

under:

```text
brainvision.observation-id.v1
```

The supplied:

```text
observation.observation_id
```

must equal the canonical derived identity exactly.

Descriptor content, semantic event class, adapter ID, adapter contract, confidence, timestamp, and world-event identity do not enter the observation-ID derivation.

A mismatch results in:

```text
INVALID_OBSERVATION_ID
```

before successor derivation or durable mutation.

---

## 13. Dynamically inert metadata

These fields may be used only for validation, provenance, replay, correlation, or diagnostics allowed by their frozen contracts:

```text
source_sequence
observation_id
adapter_id
adapter_contract_id
source_capture_time_unix_ns
confidence_q
world_event_id
```

They must not alter:

```text
F
S
W
VHE gain values
decay behavior
active visual time
Phase-7 theta
projection mathematics
```

`source_capture_time_unix_ns` is provenance only.

It must not be used as the Phase-11 observation clock.

`confidence_q` does not create an admission threshold.

No confidence policy exists in v1a.

`adapter_id` does not determine the configured lineage.

`world_event_id` does not affect VHE dynamics.

---

## 14. Semantic event boundary

The observation's:

```text
semantic_event_class
```

may be passed exactly to the frozen VHE semantic-register update.

Phase 11 defines no new semantic interpretation.

Phase 11 defines no taxonomy.

Phase 11 performs no semantic inference.

Phase 11 does not derive semantic event class from:

* text;
* memory;
* model output;
* prompts;
* world-event ID;
* adapter ID;
* confidence;
* character state.

A null semantic event class remains valid.

Low-level descriptor-only observations do not create semantic-register entries.

---

## 15. Active visual time ownership

Visual time remains entirely Brainvision-owned.

Phase 11 does not read adapter timestamps to determine visual time.

Phase 11 does not calculate elapsed time independently.

Phase 10 stages the active clock and supplies:

```text
transaction.prior_committed_active_time_ns
transaction.cutoff_active_time_ns
transaction.elapsed_active_time_ns
```

with the invariant:

```text
elapsed_active_time_ns =
cutoff_active_time_ns
-
prior_committed_active_time_ns
```

The elapsed interval must be nonnegative.

---

## 16. Critical VHE-state invariant

The fundamental runtime invariant remains:

```text
runtime.vhe_state
```

represents recursive VHE state exactly at:

```text
runtime.visual_clock.committed_active_time_ns
```

Phase 11 must preserve this invariant for every successful observation commit.

---

## 17. Exactly-one free-evolution rule

Phase 11 must not separately call:

```python
evolve_vhe_state_as_of(...)
```

before applying the observation update.

The frozen Phase-4/7 observation update owns the elapsed-time free evolution
that contributes to the committed observation successor.

Phase 10 may compute a non-adopted staged as-of VHE value while preparing the
active transaction. That staged value is internal to Phase-10 transaction
preparation. Phase 11 must not use that staged value as the observation-update
input and must not treat it as the successor state.

The normative Phase-11 successor call is:

```python
update_result = update_vhe_state_with_character_modulation(
    state=transaction.base_vhe_state,
    descriptor=observation.descriptor,
    semantic_event_class=observation.semantic_event_class,
    prior_committed_active_time_ns=
        transaction.prior_committed_active_time_ns,
    elapsed_active_time_ns=
        transaction.elapsed_active_time_ns,
    theta=transaction.configuration.theta,
)
```

For the state that is durably committed as the accepted observation successor,
exactly one elapsed-time free evolution is contributed by the frozen Phase-4/7
update path.

Phase 11 must not:

* call `evolve_vhe_state_as_of(...)` on `transaction.base_vhe_state`;
* pass an already-free-evolved state together with the same elapsed interval;
* substitute any Phase-10 non-adopted staged as-of state for
  `transaction.base_vhe_state`.

Doing so would constitute double evolution or incorrect state ownership and
would violate this specification.

---

## 18. Phase-7 modulation authority

Phase 11 obtains theta only from:

```text
transaction.configuration.theta
```

It must not derive theta from:

```text
CharacterSeed
CharacterState
MemoryGraph
memory
CognitiveCore
native kernel
SRG
Hivermind
model output
prompt content
user language
semantic_event_class
```

The frozen Phase-7 operator is authoritative.

For:

```text
theta = 0
```

the Phase-7 entry point dispatches directly to the frozen Phase-4 baseline path.

For:

```text
theta = -1 or +1
```

only the previously authorized `CONTEXT_INTEGRATION` mechanism differs.

Phase 11 itself adds no modulation mathematics.

---

## 19. Successor-time assertion

After successor derivation and before durable commit, Phase 11 must assert:

```text
update_result.event_active_time_ns
==
transaction.cutoff_active_time_ns
```

If this equality does not hold, Phase 11 must not commit the successor.

Such a failure is a successor-derivation/invariant failure.

This assertion guards the correspondence between:

* the Phase-10 staged active-time cutoff; and
* the Phase-4/7 event time embedded in the derived update result.

---

## 20. Durable commit delegation

Phase 11 commits an accepted successor only through:

```python
transaction.commit_successor(
    update_result.state,
    observation.source_sequence,
)
```

Phase 11 must not directly write:

* the VHE sidecar;
* the Brainvision configuration watermark;
* process-local runtime state.

Those remain Phase-10 responsibilities.

---

## 21. Frozen observation commit order

The accepted-observation commit order remains exactly:

```text
1. sidecar with successor VHE state and new accepted source sequence
2. configuration with matching new replay watermark
3. process-local runtime adoption
4. return success
5. later Phase-12 sink, if ever authorized
```

Phase 11 must not report `ACCEPTED` before step 3 completes successfully.

There is no Phase-12 sink in Phase 11.

---

## 22. Sidecar-write failure

If the Phase-10 sidecar write fails:

```text
configuration remains unchanged
runtime remains unchanged
acceptance is not reported
```

The observation may be retried only according to the resulting durable state and normal replay policy.

Phase 11 must not perform a second independent commit attempt inside the same admission.

---

## 23. Configuration-write failure after sidecar success

If the successor sidecar is durably written but the configuration watermark write fails:

```text
acceptance is NOT reported
the observation is NOT reapplied
process-local runtime is dropped
the durable sidecar may be ahead
```

Phase 10 exposes the failure as a recovery-required durability condition with durable partial state.

Later lazy recovery must repair:

```text
SIDECAR_AHEAD
```

by advancing the configuration watermark to the durable sidecar sequence.

After such recovery, resubmission of the original source sequence must result in:

```text
REFUSED_REPLAY
```

It must never produce a second VHE observation update.

---

## 24. Crash after both durable writes

If both durable artifacts are successfully written but the process crashes before or during process-local runtime adoption, the durable artifacts are authoritative.

Later Phase-10 recovery reconstructs runtime deterministically from those artifacts.

The observation must not be reapplied.

---

## 25. Refusal mutation rule

After Phase 10 has completed any required lazy recovery and yielded an active
transaction, every Phase-11-owned failure before `commit_successor(...)`
preserves:

```text
sidecar bytes
configuration bytes
durable replay watermark
live runtime VHE state
live committed visual-clock state
```

except for internal process-local transaction staging that is not adopted.

This guarantee does not suppress or roll back a required Phase-10 recovery
that occurs before the transaction yields.

In particular, `SIDECAR_AHEAD` recovery may advance the configuration watermark
before Phase-11 admission checks begin. That recovery is a Phase-10
reconciliation mutation, not a Phase-11 ingress mutation.

A required Phase-10 recovery occurring before transaction yield must invoke no:

```text
Phase-11 successor derivation
Phase-11 observation commit
Phase-11 acceptance receipt
Phase-12 sink
```

For an already reconciled active transaction, the following Phase-11 failures
are non-mutating:

```text
malformed observation
stream mismatch
adapter-contract mismatch
replay
invalid observation identity
successor derivation failure
successor-time assertion failure
```

---

## 26. Phase-11 result model

Phase 11 recognizes one success outcome:

```text
ACCEPTED
```

and distinct Phase-11-owned failure classes corresponding to:

```text
MALFORMED_OBSERVATION
STREAM_IDENTITY_MISMATCH
ADAPTER_CONTRACT_MISMATCH
REFUSED_REPLAY
INVALID_OBSERVATION_ID
SUCCESSOR_DERIVATION_FAILURE
```

The exact exception class implementation may be one closed ingress exception carrying:

```text
field
reason
```

or an equally strict representation.

The reason identities must remain distinguishable.

Phase 11 must not collapse replay into generic validation failure.

Phase 11 must not collapse durability or recovery failures into malformed observation.

---

## 27. Propagated Phase-10 failures

Phase-10 lifecycle/recovery failures remain Phase-10 failures.

Phase 11 must not semantically reinterpret them.

Examples include:

```text
unknown_agent
agent_identity_invalid
configuration_absent
inactive lifecycle
sidecar_missing
sidecar_integrity_failure
configuration_sidecar_incompatible
config_ahead
recovery_required
durability_failure
runtime/recovery failures
```

Their exact frozen Phase-10 reason vocabulary remains authoritative.

---

## 28. Minimal acceptance receipt

A successful Phase-11 admission returns a minimal immutable receipt only after the Phase-10 durable commit completes.

The receipt contains exactly the information needed to identify the accepted commit:

```text
observation_id
source_sequence
committed_active_time_ns
```

It must not expose:

```text
raw VHE state
Fast Trace
Persistent Context
Semantic Register internals
projection
write gate
character interpretation
emotion
attention
consciousness
memory state
kernel state
model state
```

The committed active time is obtained from the successful Phase-10 commit result.

---

## 29. No Phase-12 output surface

Phase 11 contains no sink.

It does not emit a projection event.

It does not emit a null sink event.

It does not emit a test sink event.

It does not create a downstream cognition payload.

It does not call a model.

It does not create memory.

The acceptance receipt is the Phase-11 API return value only.

Phase 12 separately owns null/test sink behavior.

---

## 30. Isolation from ordinary TORMENT

Phase-11 production code must not import or call ordinary TORMENT systems except the narrow Phase-10 lifecycle manager dependency required for the transaction boundary.

In particular, Phase 11 must not depend on or mutate:

```text
torment_service.memory_kernel
MemoryGraph
CharacterSeed
CharacterState
CognitiveCore
SRG
Hivermind
model/prompt code
ordinary ingest
retrieval
memory formation
Spine
```

No behavior in those systems changes when Phase 11 is installed.

When Brainvision is disabled or absent, ordinary TORMENT semantics remain unchanged.

---

## 31. No new scientific interpretation

Phase-11 acceptance means only:

> The typed firsthand visual observation passed the frozen Brainvision lineage and replay checks, produced a lawful frozen VHE successor, and was durably committed.

It does not establish:

* emotion;
* attention;
* awareness;
* consciousness;
* subjective experience;
* semantic understanding;
* memory duration;
* physical-world visual accuracy;
* general computer vision capability;
* model usefulness;
* cognitive integration.

`CONTEXT_INTEGRATION` remains the exact Phase-7 modulation name.

---

## 32. Required Phase-11 test matrix

Implementation acceptance must include a bounded deterministic Phase-11 test suite covering at least the following.

### A. Typed boundary

1. Exact `FirsthandVisualObservationV1` accepted as an admissible API type.
2. Raw dict refused.
3. Arbitrary object refused.
4. No alternate Phase-11 observation parser exists.
5. No second DTO exists.
6. A subclass of `FirsthandVisualObservationV1` is refused, proving the exact
   `type(observation) is FirsthandVisualObservationV1` boundary.

### B. Known-agent and lock safety

7. Unknown agent is refused.
8. Unknown-agent refusal creates no lock.
9. Unknown-agent refusal creates no Brainvision filesystem artifact.
10. Known-agent proof occurs before lock allocation through the frozen Phase-10 boundary.

### C. Lifecycle admission

11. Active configuration may admit an otherwise valid observation.
12. Suspended configuration refuses before operator update.
13. Disabled configuration refuses before operator update.
14. Absent configuration refuses without creation.
15. Missing required sidecar refuses.
16. A propagated configuration-ahead failure has exactly
    `field = "sequence"` and `reason = "config_ahead"`.
17. Recovery/integrity failures invoke no Phase-11 operator update.

### D. Exact admission order

18. Stream mismatch precedes adapter-contract comparison effects.
19. Adapter-contract mismatch precedes replay result.
20. Replay precedes observation-ID verification.
21. Stale sequence with forged observation ID returns replay refusal.
22. Fresh sequence with forged observation ID returns invalid-observation-ID.
23. Sequence gaps are admitted when all other requirements pass.

Forged or noncanonical observation-ID tests must begin from a valid exact-type
`FirsthandVisualObservationV1` object and tamper only its `observation_id`
inside the bounded test fixture. The tests must prove:

```text
stale sequence + tampered observation_id
-> REFUSED_REPLAY

fresh sequence + tampered observation_id
-> INVALID_OBSERVATION_ID
```

This test-only tampering is permitted solely to exercise the ingress defense
boundary and does not create a second production DTO or parser.

### E. Stream and contract isolation

24. Exact stream match accepted.
25. Stream mismatch leaves durable/runtime state unchanged.
26. Exact adapter-contract match accepted.
27. Adapter-contract mismatch leaves durable/runtime state unchanged.

### F. Replay

28. Sequence equal to watermark is refused.
29. Sequence below watermark is refused.
30. Sequence greater than watermark is eligible.
31. Replay refusal invokes no VHE update.
32. Replay refusal preserves sidecar bytes.
33. Replay refusal preserves configuration bytes.
34. Replay refusal preserves runtime VHE state.

### G. Identity

35. Canonical observation ID for a fresh sequence is accepted.
36. Forged ID is refused.
37. Noncanonical ID is refused.
38. ID refusal preserves all durable/runtime state.

### H. Exactly-one free evolution

39. Construct a state with nonzero Fast Trace.
40. Advance the deterministic Phase-10 active clock by a nonzero elapsed interval.
41. Admit one observation.
42. Prove the resulting Fast Trace reflects exactly one elapsed evolution.
43. Prove no separate Phase-11 `evolve_vhe_state_as_of()` evolution occurred.
44. Prove event time equals the Phase-10 cutoff.

### I. Phase-7 theta domain

45. Successful admission under theta `-1`.
46. Successful admission under theta `0`.
47. Successful admission under theta `+1`.
48. Theta zero path is bit-identical to frozen Phase-4 direct dispatch for the same transaction inputs.
49. Phase 11 derives no theta from another TORMENT subsystem.

### J. Dynamically inert metadata

For otherwise identical lawful observations, controlled metadata differences must prove:

50. `adapter_id` does not alter F/S/W.
51. `confidence_q` does not alter F/S/W.
52. capture timestamp does not alter F/S/W.
53. capture timestamp does not alter active visual time.
54. `world_event_id` does not alter F/S/W.
55. dynamically inert metadata does not alter Phase-7 theta.

Twin-lineage tests must prove that, when each observation is valid for its own
otherwise-equivalent configured lineage:

56. `source_sequence` and its canonically derived `observation_id` do not alter
    F/S/W, theta, or active visual time.
57. `adapter_contract_id` does not alter F/S/W, theta, or active visual time.

Where identity/replay fields necessarily differ for lawful distinct observations, tests must isolate only claims permitted by the frozen metadata-invariance contract.

The twin-lineage comparisons must use separately configured matching lineages
so that no invalid cross-lineage observation is used to claim numerical
invariance.

### K. Semantic boundary

58. Null semantic event class performs no R insertion.
59. Lawful semantic event class reaches only the frozen R path.
60. Semantic class does not alter forbidden F/S/W behavior outside the frozen operator contract.
61. Phase 11 performs no text or model semantic inference.

### L. Successful commit

62. Sidecar successor is written before configuration watermark.
63. Configuration watermark is written before runtime adoption/success.
64. Receipt is returned only after commit success.
65. Receipt observation ID equals accepted observation.
66. Receipt source sequence equals accepted sequence.
67. Receipt committed active time equals committed transaction cutoff.

### M. Sidecar failure

68. Inject sidecar-write failure.
69. Configuration bytes remain unchanged.
70. Runtime state remains unchanged.
71. No receipt is returned.
72. No sink/model/memory path is invoked.

### N. Configuration failure after sidecar success

73. Allow sidecar write.
74. Inject configuration-watermark write failure.
75. Prove no acceptance receipt.
76. Prove runtime is dropped.
77. Prove durable partial state is reported as recovery-required.
78. Trigger lazy recovery.
79. Prove `SIDECAR_AHEAD` repairs configuration watermark.
80. Resubmit original sequence.
81. Prove it is replay-refused.
82. Prove the VHE update was not applied twice.

### O. `SIDECAR_AHEAD` before a Phase-11 refusal

83. Establish a lawful `SIDECAR_AHEAD` durable state.
84. Begin Phase-11 admission.
85. Permit Phase 10 to repair the watermark before yielding the active
    transaction.
86. Cause a later Phase-11 admission refusal.
87. Prove the only durable mutation is the expected Phase-10 recovery repair.
88. Prove no Phase-11 successor update occurs.
89. Prove no Phase-11 commit occurs.
90. Prove no acceptance receipt is returned.
91. Prove no sink behavior occurs.

### P. Recovery after committed durable artifacts

92. Simulate durable sidecar/config success without process-local adoption.
93. Recover.
94. Prove deterministic runtime reconstruction.
95. Prove accepted sequence is not reapplied.

### Q. Static architectural isolation

96. No call to `Fabric.ingest`.
97. No MemoryGraph import/contact.
98. No memory-kernel import/contact.
99. No CharacterSeed/CharacterState contact.
100. No CognitiveCore contact.
101. No SRG contact.
102. No Hivermind contact.
103. No prompt/model contact.
104. No Spine contact.
105. No Phase-12 sink implementation.
106. No raw VHE state exposed in the acceptance receipt.

---

## 33. Regression requirements

Phase-11 implementation review must run:

1. Phase-11 focused tests.
2. Full Brainvision regression suite.
3. Relevant Phase-10 lifecycle/recovery tests.
4. Relevant path-security/Fabric regression tests.
5. Python compile validation.
6. `git diff --check`.

Any frozen Phase-6 or Phase-7 acceptance test invoked during regression remains:

```text
REPRODUCTION / REGRESSION ONLY
```

It must not be represented as a new formal scientific administration.

---

## 34. Implementation change boundary

Expected Phase-11 implementation scope is narrow.

Preferred new production code:

```text
brainvision/ingress.py
```

Expected tests:

```text
tests/test_brainvision_phase11_*.py
```

Phase 11 should require no semantic change to:

```text
brainvision/lifecycle.py
brainvision/vhe.py
brainvision/character_modulation.py
brainvision/configuration.py
brainvision/vhe_sidecar.py
torment_service/fabric.py
```

If implementation discovers that a semantic change to a frozen Phase-10 or earlier component is necessary, Phase-11 implementation must stop and return for architecture review.

Incidental import/export-only changes must also be reviewed before acceptance.

---

## 35. Explicitly prohibited implementation expansion

Phase 11 must not add:

* camera capture code;
* video decoding;
* image preprocessing;
* descriptor extraction;
* multi-camera merging;
* stream rebinding;
* a confidence threshold;
* a frame-rate policy;
* a wall-clock catch-up policy;
* a raw image DTO;
* alternate observation DTOs;
* memory writeback;
* projection sinks;
* cognition consumers;
* model prompts;
* LLM inference;
* Hivermind sharing;
* SRG behavior;
* automatic CharacterSeed mapping;
* Phase-12 behavior;
* v1b behavior.

Those are outside Phase 11.

---

## 36. Acceptance conditions

Phase 11 may be marked `IMPLEMENTED + ACCEPTED` only when all of the following hold:

1. This specification is frozen before implementation.
2. The implementation remains within the authorized boundary.
3. The exact admission order is preserved.
4. The typed DTO-only rule is preserved.
5. Replay precedence is preserved.
6. Sequence gaps remain valid.
7. Exactly one VHE free evolution occurs.
8. The event-time/cutoff assertion is enforced.
9. Frozen Phase-7 modulation is used exactly.
10. Sidecar-first/configuration-second transaction ordering remains unchanged.
11. Partial durable commit cannot cause duplicate VHE application.
12. Acceptance is exposed only after durable commit success.
13. No Phase-12 sink exists.
14. No ordinary TORMENT subsystem is contacted.
15. Focused tests pass.
16. Brainvision regression passes.
17. Required production/path regressions pass.
18. Compile validation passes.
19. `git diff --check` passes.
20. Review finds no unauthorized reopening of earlier phases.

---

## 37. Phase boundary after acceptance

Successful Phase-11 completion authorizes only progression to:

```text
Phase 12 — null/test sinks
```

It does not authorize v1b integration.

The frozen roadmap remains:

```text
Phase 11
direct ingress

Phase 12
null/test sinks

Phase 13
complete v1a qualification

MANDATORY HOLD

Phase 14+
governed v1b integration
```

No MemoryGraph, memory, kernel, cognition, CharacterState, SRG, Hivermind, prompt, or model integration is authorized before completion of Phase 13 and the mandatory hold followed by explicit reauthorization.

---

## 38. Claim ceiling

Phase-11 success establishes only that:

* exact typed firsthand observations can be directly admitted;
* lineage and replay rules are enforced;
* frozen VHE mathematics can derive one lawful successor;
* the successor can be durably committed under Phase-10 transaction semantics;
* crash/recovery behavior does not duplicate an admitted observation;
* the path remains isolated from ordinary TORMENT cognition and memory systems.

It does not establish:

```text
physical vision accuracy
semantic understanding
emotion
attention
awareness
consciousness
memory formation
memory duration
model utility
cognitive utility
multi-stream behavior
arbitrary frame-rate invariance
v1b integration correctness
```

---

## 39. Pre-freeze decision

Required review result before implementation:

```text
PHASE_11_SPECIFICATION_REVIEW:
PASS
```

Only after that result may this document status be changed from:

```text
PRE-FREEZE CANDIDATE
```

to:

```text
FROZEN PRE-IMPLEMENTATION PHASE-11 SPECIFICATION
```

Implementation must begin from the exact commit containing the frozen specification.
