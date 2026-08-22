# TORMENT Brainvision — Phase 13 Complete v1a Qualification Specification v1.0

## Status and authority

**FROZEN PRE-ADMINISTRATION PHASE-13 v1a QUALIFICATION SPECIFICATION**

This document defines the final assembled-product qualification for TORMENT Brainvision v1a.

Phase 13 is not a feature-development phase. It adds no new Brainvision capability and authorizes no production behavior change.

Its purpose is:

> To determine, under a fully preregistered deterministic administration, whether the assembled Brainvision v1a implementation satisfies its frozen bounded product contract end-to-end.

Authoritative pre-Phase-13 baseline:

```text
2da8f560b585acfc660f18f2de2945a1050a81aa
```

Phase 13 consumes the frozen scientific and implementation authority of Phases 0–12.

It does not reopen those phases merely because their behavior is reproduced through the assembled path.

Expected Phase-13 production-code change count:

```text
0
```

Phase 13 may add only qualification specification, test/harness, preregistration, evidence, and result artifacts.

If qualifying v1a requires changing production Brainvision behavior, Phase 13 must stop and report the failure or architecture conflict rather than changing the system under qualification.

---

# 1. Terminal roadmap position

Current roadmap:

```text
Phase 0   FROZEN
Phase 1   FROZEN
Phase 2   FROZEN
Phase 3   FROZEN
Phase 4   FROZEN
Phase 5   FROZEN
Phase 6   PASS + FROZEN
Phase 7   formal first administration PASS + FROZEN
Phase 8   IMPLEMENTED + ACCEPTED
Phase 9   IMPLEMENTED + ACCEPTED
Phase 10  IMPLEMENTED + ACCEPTED
Phase 11  IMPLEMENTED + ACCEPTED
Phase 12  IMPLEMENTED + ACCEPTED
Phase 13  FINAL v1a QUALIFICATION
```

There is no automatically authorized Phase 14 after Phase 13.

A Phase-13 PASS terminates v1a development at:

```text
BRAINVISION_V1A:
QUALIFIED

MANDATORY_HOLD:
ACTIVE
```

The HOLD is cleared only by a separately recorded explicit authorization identifying the later scope released.

---

# 2. Qualification object

The system under qualification is the assembled v1a path:

```text
typed FIRSTHAND_VISUAL observation
        ↓
Phase-11 direct ingress
        ↓
Phase-10 lifecycle / active transaction
        ↓
Phase-7 character-modulated Phase-4 recursive update
        ↓
Phase-9 sidecar-first persistence
        ↓
Phase-8 configuration watermark persistence
        ↓
Phase-10 runtime adoption / recovery
        ↓
Phase-12 commit-time Phase-5 projection
        ↓
detached diagnostic sink payload
```

The qualification does not attach a cognitive consumer.

The system under qualification still has no:

```text
ordinary Fabric.ingest route
MemoryGraph write
memory formation
memory retrieval
native memory-kernel contact
CharacterSeed derivation
CharacterState mutation
CognitiveCore integration
SRG integration
Hivermind integration
Spine integration
prompt construction
model inference
LLM inference
```

---

# 3. Evidence-authority hierarchy

Phase 13 distinguishes four evidence classes.

## Category A — frozen authority

A prior frozen scientific or exact-contract result remains authoritative.

Phase 13 may reproduce it but may not present the reproduction as new scientific evidence.

Includes:

* Phase-2 DTO/fixture/identity algebra;
* Phase-3 clock primitive;
* Phase-4 recursive operator;
* Phase-5 projection/quantization;
* Phase-6 300-active-second formal result;
* Phase-7 formal `CONTEXT_INTEGRATION` result;
* frozen identities and acceptance relations.

A mismatch against Category-A authority is a v1a implementation/conformance failure unless the frozen authority itself is formally reopened.

## Category B — regression/reproduction

Existing accepted behavior may be rerun as regression or reproduction evidence.

A Phase-13 result must label such evidence:

```text
REPRODUCTION / REGRESSION ONLY
```

It must not be described as a new formal Phase-6 or Phase-7 administration.

## Category C — composed-path qualification

A frozen component claim must be exercised through the actual assembled Phase-11/12 path to show that integration preserves it.

Examples:

* retained-history survival through real configuration, clock, persistence, ingress, and sink;
* modulation profile binding through durable configuration;
* restart/reload continuation through the complete path;
* replay refusal with sink attached.

## Category D — assembled-only evidence

Only the fully assembled product can establish these properties:

* sink purity;
* assembled restart/recovery equivalence;
* composed replay protection;
* full-path deterministic reproduction;
* anti-self-grading separation;
* absence of duplicate application across failure/recovery boundaries.

---

# 4. Scientific-claim inheritance rule

Phase 13 must not restate a Category-A claim as a newly discovered Phase-13 scientific result.

Where frozen science is exercised through the assembled path, the result is phrased as:

> The assembled v1a path reproduced the frozen expected behavior.

A mismatch is a qualification failure.

It is never permission to:

* tune a fixture;
* alter a threshold;
* change a projection quantum;
* modify a frozen identity;
* reinterpret a failed result.

---

# 5. Qualification blocks

The formal qualification contains exactly twelve required blocks:

```text
E1   Retained-history endpoint
E2   Order-sensitive endpoint
E3   Metadata inertness
E4   Semantic isolation
E5   Character-modulation reproduction
E6   Restart/reload continuation
E7   Crash/recovery matrix
E8   Replay protection
E9   Pure-read independence
E10  Assembled lifecycle matrix
E11  Sink purity
E12  Whole-run determinism
```

A valid PASS requires all E1–E12.

No block may be silently omitted.

---

# 6. Phase-13 deterministic clock

All formal Phase-13 administrations use an injected schedule-driven monotonic source.

The qualification clock must be **idempotent under repeated sampling**.

Conceptually:

```python
clock.set_active_time_ns(T)
```

causes every monotonic sample to return the value corresponding to `T` until the harness explicitly changes it.

Repeated Brainvision sampling must not itself advance time.

Forbidden clock design:

```text
read clock
→ increment test time
→ return next value
```

Required property:

```text
number of monotonic clock reads
has no effect on the scheduled active time
```

This is mandatory for:

* E9 read purity;
* E11 sink purity;
* E12 determinism;
* lifecycle comparisons;
* replay/no-residue comparisons.

The harness owns all schedule changes explicitly.

Wall-clock duration is not part of qualification.

---

# 7. Exact time representation

Qualification schedules use exact integer nanoseconds.

Canonical anchors include:

```text
0 s   = 0 ns
1 s   = 1_000_000_000 ns
2 s   = 2_000_000_000 ns
3 s   = 3_000_000_000 ns
301 s = 301_000_000_000 ns
```

No floating time values enter the formal administration.

---

# 8. E1 — retained-history endpoint

## 8.1 Frozen Phase-0 fixture preservation

The frozen Phase-0 histories must not be shortened or rewritten.

The original histories remain:

```text
H0:
d0 @ t=0
d0 @ t=1
d0 @ t=2

H1:
d0 @ t=0
dA @ t=1
d0 @ t=2
```

Phase 0 originally samples them with a pure projection read at:

```text
t=301
```

Phase 12 intentionally exposes only commit-time projections.

Phase 13 therefore appends one lawful sink-compatible sampling observation:

```text
d0 @ t=301
```

The full Phase-13 administrations are:

```text
H0:
d0 @ 0
d0 @ 1
d0 @ 2
d0 @ 301   ← Phase-13 sampling probe

H1:
d0 @ 0
dA @ 1
d0 @ 2
d0 @ 301   ← Phase-13 sampling probe
```

The frozen `t=2` observation is preserved exactly.

## 8.2 Sampling-probe equivalence

For frozen `d0`:

```text
mean_luminance_q = 500000
mean_adjacent_luminance_difference_q = 0
```

the frozen Phase-4 normalization gives:

```text
u1 = 0
u2 = 0
```

Therefore:

```text
write_gate_q = 0
```

and the sampling observation performs:

```text
no Persistent Context write
```

With:

```text
semantic_event_class = None
```

it performs:

```text
no Semantic Register update
```

Its fast trace is canonically zero.

At `t=301`, the prior event fast trace has already expired.

Since Persistent Context has no elapsed-time decay, the Semantic Register is unchanged by a null-class observation, and the appended observation's own Fast Trace is canonically zero at its commit-time read, the appended `d0@301` commit produces the same six Phase-5 projection-role values that the frozen pure read would have produced at that time.

This equivalence is asserted over the six Phase-5 projection roles only.

The appended observation is a durable commit and therefore also advances the replay watermark by one and records `committed_active_time_ns = 301_000_000_000` in the VHE sidecar, neither of which the frozen pure read would have done.

Those durable differences are outside the retained-history criterion and must not be compared against the frozen pure-read administration.

## 8.3 E1 preregistered predictions

The expected-result manifest must freeze at minimum:

```text
H0 current_activity_code = 0
H1 current_activity_code = 0

H0 present_history_relation_code = 0
H1 present_history_relation_code = 0

H0 retained_history_code = 0
H1 retained_history_code = 8
```

The terminal current-activity equality is explicitly classified as:

```text
DEGENERATE_TERMINAL_D0_CONTROL
```

because `d0` zeros Fast Trace by construction.

It must not be represented as an independently informative matched-current control.

## 8.4 E1 acceptance relation

Use the frozen Phase-5 role field sets.

Required:

```text
CURRENT_ACTIVITY_ROLE:
equal canonical encoded value
expected exactly 0

RETAINED_HISTORY_ROLE:
distinguishable
```

The acceptance relation is the frozen:

```text
WITHIN_PROJECTION_QUANTUM
```

meaning exact equality of the canonical encoded relevant field set.

There is no floating tolerance.

The retained-history separation criterion remains the previously frozen criterion; Phase 13 must not invent a new stronger threshold.

Observed expected reproduction:

```text
retained_history_code:
H0 = 0
H1 = 8
```

may be recorded, but the scientific role criterion remains the frozen Phase-0/5 criterion.

---

# 9. E2 — order-sensitive endpoint

The frozen order histories are administered without modification:

```text
O1:
d0 @ 0
dA @ 1
dB @ 2
d0 @ 3

O2:
d0 @ 0
dB @ 1
dA @ 2
d0 @ 3
```

The terminal `d0@3` commit itself is the lawful Phase-12 sample.

Both arms use:

* identical active-time schedule;
* identical source-sequence structure;
* identical stream identity;
* identical adapter contract;
* `theta = 0`;
* no semantic event class.

The only intended dynamical difference is the order of `dA` and `dB`.

## E2 preregistered predictions

At minimum:

```text
O1 current_activity_code = 0
O2 current_activity_code = 0

O1 present_history_relation_code = 0
O2 present_history_relation_code = 0

O1 trajectory_code = +5
O2 trajectory_code = -5
```

The current-activity equality is again explicitly marked:

```text
DEGENERATE_TERMINAL_D0_CONTROL
```

The sole preregistered order-sensitivity acceptance field is:

```text
trajectory_code
```

It must differ.

No additional numeric separation floor is introduced.

The frozen auxiliary reproduction predictions are:

```text
O1 retained_history_code = 8
O2 retained_history_code = 8
```

Both are classified:

```text
AUXILIARY REPRODUCTION PREDICTION
NOT E2 ACCEPTANCE FIELD
```

`trajectory_code` is the unique discriminating Phase-5 projection field for the frozen O1/O2 fixture; the other five projection roles are equal across the two arms.

The equal auxiliary `retained_history_code` values do not alter the preregistered E2 acceptance predicate and must not be used to claim that retained history is order-insensitive in general.

They must not be selected after observing Phase-13 results.

---

# 10. E3 — metadata inertness

E3 proves that metadata frozen as dynamically inert remains dynamically inert through the assembled path.

Use lawful twin-lineage administrations.

## Direct inert metadata twins

Vary only:

```text
adapter_id
source_capture_time_unix_ns
confidence_q
world_event_id
```

while preserving the same descriptor sequence, clock schedule, configuration dynamics, and semantic class.

Required where applicable:

```text
canonical sidecar bytes:
BIT_IDENTICAL

canonical projection bytes:
BIT_IDENTICAL

later controlled projection bytes:
BIT_IDENTICAL
```

Configuration bytes may differ only if the tested field is itself lawfully persisted; fields not persisted in configuration must not create a configuration difference.

## Source-sequence / observation-ID twin

Because observation ID binds sequence, compare lawful offset-sequence twin lineages.

Require:

```text
final canonical projection bytes:
BIT_IDENTICAL
```

while allowing intentional differences in:

```text
receipt source_sequence
receipt observation_id
configuration watermark
sidecar accepted sequence
```

A separate fresh-sequence forged-ID administration must produce:

```text
INVALID_OBSERVATION_ID
```

without dynamical mutation.

## Adapter-contract twin

Use two separately valid lineages that differ only in:

```text
adapter_contract_id
```

while receiving identical exact Phase-2 descriptor DTOs.

Require Brainvision dynamical/projection equality.

This establishes only:

> the adapter-contract identifier itself is an admission/lineage field and does not numerically drive Brainvision.

It does **not** establish physical or numerical equivalence between different real-world measurement contracts.

---

# 11. E4 — semantic isolation

Use matched lawful observations differing only in:

```text
semantic_event_class
```

with a frozen descriptor schedule.

Through the Phase-12 projection surface require exact equality for the sink-visible dynamical fields:

```text
current_activity_code
retained_history_code
present_history_relation_code
trajectory_code
```

Only the frozen R-derived fields may differ:

```text
open_event_class
recurrence_code
```

Phase 13 must not claim that sink evidence alone proves raw F/S/W bit identity.

Raw F/S/W semantic isolation remains frozen Phase-4/6 authority.

E4 establishes only that the assembled projection path reproduces that isolation at the authorized external observable.

---

# 12. E5 — character-modulation reproduction

Phase 7 remains the sole formal scientific authority for:

```text
CONTEXT_INTEGRATION
```

Phase 13 performs composed-path reproduction only.

Use exactly three independent Brainvision configuration lineages, one per theta arm:

```text
theta = -1
theta = 0
theta = +1
```

Each configuration must carry the exact frozen mapping/profile identities.

Do not mutate theta while active or suspended.

The expected-result manifest must bind each arm to its workspace/agent test identity, stream identity, adapter-contract identity, theta, and modulation profile ID. The Phase-13 administration uses one identical stream identity across all three distinct agent lineages; the current identity/configuration boundary permits that value without cross-lineage coupling.

The run ledger externally binds each arm to its theta/profile identity because Phase-5 projection payloads are intentionally theta-blind.

## Frozen reproduction predictions

For the retained-history H1 construction at the 300-active-second sample:

```text
theta -1 → retained_history_code = 6
theta  0 → retained_history_code = 8
theta +1 → retained_history_code = 10
```

For the corresponding H0 arms:

```text
current_activity_code = 0
retained_history_code = 0
```

The expected-result manifest must reference the frozen Phase-7 expected record and profile IDs.

Phase 13 must not derive new expected modulation values.

No new theta value, fixture, threshold, mapping, or interpretation is permitted.

Any such run is outside Phase 13 and invalid.

---

# 13. E6 — restart/reload continuation

E6 compares:

```text
CONTROL:
uninterrupted execution

RESTART:
identical execution, but process-local Brainvision manager/host state is destroyed after accepted commit k and rebuilt over the same durable data before commit k+1
```

Both use the same deterministic active-time schedule. E6 freezes:

```text
DELTA_DOWN_NS = 10_000_000_000
```

with `DELTA_DOWN_NS > 0`.

The restart administration is exactly:

```text
commit observation k at cutoff T_k
→ close the Phase-12 host
→ destroy process-local lifecycle-manager/runtime ownership
→ advance the injected qualification clock by DELTA_DOWN_NS
→ construct a fresh lifecycle manager over the same durable data root
→ construct a new lawful Phase-12 host
→ advance only by the next scheduled ACTIVE interval DELTA_ACTIVE_NS
→ commit observation k+1
```

The rebuilt manager observes the later monotonic source value but rebases from the durable committed active time. Process downtime does not advance Brainvision active visual time in v1a.

Required after the restart boundary:

```text
configuration canonical bytes:
BIT_IDENTICAL at equivalent commit points

sidecar canonical bytes:
BIT_IDENTICAL at equivalent commit points

Phase-11 receipts:
exact equality

Phase-5 canonical projection bytes:
BIT_IDENTICAL

replay watermark:
exact equality
```

`DELTA_DOWN_NS` must appear in none of:

```text
receipt committed_active_time_ns
sidecar committed_active_time_ns
Phase-5 projection
replay watermark
```

The `k+1` committed active time must equal the uninterrupted control's corresponding active-time result and must exclude `DELTA_DOWN_NS`.

The committed active time carried in the sidecar must continue exactly.

The process-local monotonic origin is not serialized.

## Sink-sequence scope

Sink delivery is intentionally not persisted or backfilled.

Therefore Phase 13 does not require the complete pre/post-restart sink record lists to be identical as whole lists.

Required relation:

> The restarted run's sink-record suffix after host reconstruction is bit-identical to the corresponding suffix of the uninterrupted control.

No missing pre-restart sink record is reconstructed after reload.

---

# 14. E7 — crash/recovery matrix

E7 contains five required branches.

## E7.1 Sidecar-write failure

Inject sidecar persistence failure before the sidecar commit succeeds.

Expected:

```text
durable_committed = False
no configuration watermark advance
sidecar bytes unchanged
configuration bytes unchanged
runtime committed state unchanged
no Phase-12 sink delivery
no receipt
```

The same sequence may be lawfully retried because no durable observation was accepted.

## E7.2 Configuration-write failure after sidecar success

Allow successor sidecar persistence, then fail configuration watermark persistence.

Expected Phase-10 failure:

```text
field = "configuration"
reason = "recovery_required"
durable_committed = True
```

Required:

```text
no success receipt
no sink delivery
runtime dropped
sidecar ahead durably
```

On later access:

```text
SIDECAR_AHEAD
```

is repaired by advancing configuration watermark to the durable sidecar sequence.

The accepted observation is never reapplied.

Resubmission of the same sequence produces:

```text
REFUSED_REPLAY
```

No sink backfill occurs.

## E7.3 SIDECAR_AHEAD recovery in isolation

Start from a valid deliberately constructed `SIDECAR_AHEAD` durable pair.

First recovery access performs exactly one lawful repair.

A second recovery access performs no additional repair.

After reconciliation:

```text
configuration bytes:
stable / BIT_IDENTICAL across subsequent accesses
```

No synthetic sink event is generated.

## E7.4 Both durable writes succeed before runtime adoption

E7.4 uses this exact test-only fault instrument:

```text
wrap the Phase-10 configuration-write primitive
→ perform the real configuration write successfully
→ only after that durable write completes, raise before runtime adoption
```

The expected externally observed error is intentionally identical to E7.2:

```text
field = "configuration"
reason = "recovery_required"
durable_committed = True
```

E7.2 and E7.4 are distinguished by durable evidence, not merely by the error object:

```text
E7.2:
sidecar durable
configuration watermark not advanced
durable pair = SIDECAR_AHEAD
next recovery performs watermark repair

E7.4:
sidecar durable
configuration watermark durable
durable pair = EQUAL / mutually consistent
next recovery performs no SIDECAR_AHEAD repair
```

After the injected post-write exception, destroy the current manager/host and construct a fresh manager over the durable data root. This is the preferred crash analogue: recovery treats the durable artifacts as authoritative after loss of process-local state.

Require:

```text
configuration bytes unchanged by unnecessary repair
committed sequence replay-refused
continuation at k+1 BIT_IDENTICAL to uninterrupted control
no duplicate VHE update
no sink backfill for interrupted observation
```

The E7.4 verdict depends on durable artifact bytes/hashes, compatibility relation, absence of a repair write, continuation, and replay outcome.

## E7.5 Phase-12 post-commit interruption before delivery

E7.5 uses the existing throwing-sink path only. It must not induce a projection-construction failure.

```text
sink.on_projection(...) raises after the observation has durably committed
```

Expected:

```text
durable artifacts remain authoritative
no rollback
no retry
no recovery backfill
same sequence replay-refused
no duplicate VHE update
```

The unchanged receipt returns. For the single characterized delivery, the expected Phase-12 metrics are:

```text
sink_invocations_total = 0
sink_delivery_failures_total = 1
projection_construction_failures_total = 0
```

This administration characterizes post-commit callback-delivery failure; it is not literal process termination. In the throwing-sink case, the returned receipt, delivery-failure metric, durable artifacts, and run ledger survive.

For literal process death between durable commit and delivery, no returned receipt, process-local metric, or sink record survives. The durable postconditions remain: the commit is authoritative, there is no rollback, replay bypass, duplicate VHE update, or recovery sink backfill. Any missing delivery can be attributed only through the independent Phase-13 run ledger and fault ledger.

Literal process death need not be separately executed if the formal E7.4/E7.5 evidence package establishes these durable semantics and ledger attribution.

The test seam must not become a production delivery-recovery mechanism.

`projection_construction_failures_total = 0` remains a hard requirement throughout every formal Phase-13 administration.

---

# 15. Phase-13 run ledger requirement

Because some crash branches can create a durably accepted observation with no sink record, sink records alone are insufficient evidence.

The formal run ledger must contain one entry for every attempted:

```text
admit()
lifecycle operation
recovery-triggering operation
```

Each ingress entry records either:

## Success

```text
observation_id
source_sequence
committed_active_time_ns
```

or:

## Failure

```text
error class
field
reason
durable_committed where available
```

This ledger is generated by the Phase-13 harness.

It is not a production Brainvision artifact.

---

# 16. E8 — replay protection

Required replay branches:

```text
source_sequence == current watermark
source_sequence < current watermark
same committed observation after clean reload
same committed sequence after SIDECAR_AHEAD recovery
```

All must produce the exact frozen replay refusal.

Required:

```text
sidecar bytes:
BIT_IDENTICAL

configuration bytes:
BIT_IDENTICAL

Phase-12 metrics:
unchanged

sink delivery:
none

receipt:
none
```

The next lawful observation under the same controlled schedule must produce a projection bit-identical to a control run in which the refused replay was never attempted.

Also administer:

```text
source_sequence > watermark
but invalid observation_id
```

Expected:

```text
INVALID_OBSERVATION_ID
```

with the same no-residue properties.

---

# 17. E9 — pure-read independence

Phase 13 must not add a Phase-12 query API.

The existing Phase-10:

```text
runtime_snapshot()
```

may be used only as a **stimulus**.

Its returned raw snapshot must be discarded.

Phase-13 code must not:

```text
read snapshot.vhe_state
compare snapshot.vhe_state
hash snapshot.vhe_state
serialize snapshot.vhe_state
log snapshot.vhe_state
record snapshot.vhe_state
derive an acceptance criterion from snapshot.vhe_state
```

The same prohibition applies to raw F/S/R fields obtained by any equivalent internal surface.

## E9.1 Reconciled read scheduling

Compare arms performing the same deterministic schedule while calling `runtime_snapshot()`:

```text
0 times
1 time
7 times
```

between equivalent observations.

Required:

```text
sidecar bytes:
BIT_IDENTICAL

configuration bytes:
BIT_IDENTICAL

receipt committed_active_time_ns:
exact equality

replay watermark:
exact equality

later Phase-12 canonical projection bytes:
BIT_IDENTICAL
```

## E9.2 Unreconciled read access

On an unreconciled `SIDECAR_AHEAD` pair, first access may legitimately cause the frozen Phase-10 watermark repair.

Therefore the Phase-13 read-purity claim is:

> For a reconciled durable pair, read scheduling is byte-inert. For an unreconciled `SIDECAR_AHEAD` pair, first access of any kind may perform one deterministic, idempotent watermark repair; subsequent accesses are byte-inert.

E9 must prove both halves separately.

---

# 18. E10 — assembled lifecycle matrix

E10 exercises only lifecycle behavior whose composed-path interaction is relevant.

Required scenarios include:

## Enable

```text
disabled configuration
→ enable
→ active
→ lawful observation accepted
→ sink record produced if sink configured
```

## Suspend

```text
active
→ suspend
→ frozen committed active time
→ advance qualification clock by DELTA_SUSP_NS while suspended
→ observation refused
→ no projection/sink delivery
```

E10 freezes:

```text
DELTA_SUSP_NS = 10_000_000_000
```

with `DELTA_SUSP_NS > 0`.

## Resume

```text
suspended
→ resume
→ active
→ advance qualification clock by DELTA_ACTIVE_NS while active
→ later lawful observation accepted
→ continuation valid
```

For an active committed time `T_s` at suspension, the next lawful observation must have:

```text
next_committed_active_time_ns = T_s + DELTA_ACTIVE_NS
```

and explicitly not:

```text
T_s + DELTA_SUSP_NS + DELTA_ACTIVE_NS
```

`DELTA_SUSP_NS` must appear in none of the receipt committed active time, sidecar committed active time, or Phase-5 projection timing. The suspended interval is excluded from Brainvision active visual time. A zero-duration suspension cannot satisfy this E10 criterion.

## Reset

```text
active or suspended
→ reset
→ fresh recursive state
→ active time zero as frozen
→ replay watermark preserved
```

Previously accepted sequences remain replay-refused.

## Disable

```text
active/suspended
→ disable
→ configuration retained
→ replay watermark retained
→ sidecar removed
→ runtime removed
```

Observation mutation is refused while disabled.

## Re-enable

```text
disabled
→ enable
→ fresh VHE continuation
→ prior replay watermark preserved
```

Only a greater source sequence may be accepted.

Earlier isolated transition validation remains Phase-10 authority/regression.

E10 exists to prove that ingress/sink attachment did not alter the lifecycle semantics.

---

# 19. E11 — sink purity

E11 compares equivalent fresh arms under identical idempotent clock schedules.

The Phase-13 schedule-driven idempotent clock fully removes sink wall-clock latency from all committed Brainvision quantities during formal qualification. The sink may delay real execution, but repeated clock sampling returns the same harness-set value until the harness explicitly advances it. Therefore null, recording, and throwing-sink arms remain comparable under an identical active-time schedule.

Required sink conditions:

```text
S0  sink=None
S1  recording sink
S2  throwing sink
```

Phase-12 unit evidence remains authoritative for deliberately injected projection-construction failure semantics.

Formal Phase-13 runs must require:

```text
projection_construction_failures_total = 0
```

in every arm.

A nonzero value is a qualification failure.

Do not corrupt VHE state merely to force this counter during formal administration.

## E11 durable comparisons

Across S0/S1/S2 require, at equivalent commits:

```text
sidecar bytes:
BIT_IDENTICAL

configuration bytes:
BIT_IDENTICAL

Phase-11 receipts:
exact equality

replay watermark:
exact equality
```

For future-projection purity, each arm must eventually produce a lawful Phase-12 recording under an identical controlled schedule after the compared sink behavior.

The resulting later canonical projection bytes must be:

```text
BIT_IDENTICAL
```

This may be accomplished by closing the existing bound host after the compared segment and constructing a lawful replacement recording host for the same lineage.

No raw-state comparison is permitted.

## Expected Phase-12 metrics

For a recording-sink arm with N successful deliveries:

```text
sink_invocations_total = N
sink_delivery_failures_total = 0
projection_construction_failures_total = 0
```

For a throwing-sink arm with N delivery attempts:

```text
sink_invocations_total = 0
sink_delivery_failures_total = N
projection_construction_failures_total = 0
```

For the null arm:

```text
all Phase-12 metrics = 0
```

---

# 20. E12 — whole-run determinism

E12 uses two independently initialized fresh qualification arms with:

```text
identical fixture sequence
identical lifecycle schedule
identical configuration
identical theta
identical deterministic clock schedule
identical fault-free administration
```

Required exact reproduction:

```text
Phase-11 receipt sequence:
exact equality

Phase-5 canonical projection-byte sequence:
BIT_IDENTICAL

sidecar canonical bytes at equivalent commit points:
BIT_IDENTICAL

configuration canonical bytes at equivalent commit points:
BIT_IDENTICAL

replay outcome sequence:
exact equality

Phase-12 metrics:
exact equality
```

The determinism claim is bounded to the preregistered schedules and environment actually administered.

It does not establish universal determinism over every possible schedule or platform.

If qualification is performed on one platform only, the result must say so.

Cross-platform determinism may be reported only if actually administered.

---

# 21. Comparison relations

Phase 13 may use only frozen comparison relations.

## BIT_IDENTICAL

Used for:

* deterministic repeats;
* metadata twins where the tested metadata is dynamically inert;
* exact persistence/restart continuation;
* sink-purity durable comparisons;
* refused-replay artifact preservation;
* reconciled pure-read scheduling;
* canonical projection-byte determinism where whole canonical values are expected equal.

## WITHIN_PROJECTION_QUANTUM

This is not numerical tolerance.

It means exact equality of the frozen canonical encoded representation over the preregistered relevant field set.

Used for the frozen Phase-0/5 role comparisons, including:

```text
retained-history current equality
retained-history distinction
order-current equality
order-history distinction
```

## Exact receipt equality

Compare:

```text
observation_id
source_sequence
committed_active_time_ns
```

as exact values.

## Exact failure equality

Compare frozen:

```text
error type
field
reason
durable_committed where defined
```

No approximate or semantic matching is allowed.

---

# 22. Projection determinism representation

The normative deterministic representation for Phase-5 projections is the existing frozen canonical serialization.

Phase 13 compares:

```python
projection_a_canonical_bytes == projection_b_canonical_bytes
```

For Phase-12 detached mappings, the harness must serialize them using the frozen Phase-5 canonical mapping/serialization contract.

Plain Python dictionary equality is not the normative determinism relation.

Phase 13 creates no new projection serialization identity.

---

# 23. Anti-self-grading boundary

Production Brainvision may supply only its existing lawful outputs:

```text
Phase-11 receipts
Phase-12 detached projection mappings
Phase-12 metrics
durable configuration bytes
durable sidecar bytes
typed errors
```

The test-only Phase-13 harness owns:

```text
expected values
expected relations
expected role field sets
fixture administration
clock schedule
fault schedule
artifact hashing
acceptance predicates
block verdicts
final verdict
```

No expected value or final pass/fail predicate may be added to:

```text
brainvision/
Phase12 sink implementation
lifecycle manager
projection implementation
production ingress
```

The existing Phase-5 comparison primitive and relevant-field-set definitions may be imported by the test harness because they define frozen comparison semantics rather than expected outcomes.

---

# 24. Raw-state prohibition

No Phase-13 evidence artifact may contain:

```text
FastTrace
amplitude_1_q
amplitude_2_q
remaining_ns
PersistentContext raw coordinates
SemanticRegister raw entries
raw VheState
write_gate_q
clamped_orientation_q
internal gains
raw normalized descriptor intermediates
process-local monotonic origin
```

Raw state remains lawful inside earlier component-level tests but is excluded from the formal Phase-13 evidence package.

Qualification is performed against the bounded external observables and frozen durable artifact bytes.

---

# 25. Expected-result manifest

Before first administration, Phase 13 must freeze a machine-readable expected-result manifest.

The manifest contains, per E1–E12 block:

```text
administration identity
fixture identity
configuration/profile identity
clock schedule
lifecycle schedule
fault schedule if applicable
expected receipts or receipt relation
expected projection fields/codes or relation
expected artifact relation
expected error field/reason where applicable
expected Phase-12 metrics
acceptance relation
claim classification
```

The manifest must include the exact predicted:

```text
E1:
current_activity_code = 0
present_history_relation_code = 0
H0 retained_history_code = 0
H1 retained_history_code = 8

E2:
current_activity_code = 0
present_history_relation_code = 0
O1 trajectory_code = +5
O2 trajectory_code = -5
O1 retained_history_code = 8
O2 retained_history_code = 8

E5:
theta -1 retained_history_code = 6
theta  0 retained_history_code = 8
theta +1 retained_history_code = 10
```

The E2 retained-history values are `AUXILIARY REPRODUCTION PREDICTION / NOT E2 ACCEPTANCE FIELD`; only `trajectory_code` is the E2 order-sensitivity acceptance field.

---

# 26. Authority guard

Before formal administration, the qualification harness must verify exact authority bindings.

At minimum:

```text
repository HEAD
origin/main
worktree cleanliness
Phase-13 specification hash
fixture-manifest hash
expected-result-manifest hash

Phase-2 fixture hashes
observation schema identity
observation-ID schema identity
operator identity
projection identity
projection schema identity
rounding algorithm identity
modulation schema identity
modulation mapping identity
modulation profile-schema identity
all theta-arm modulation profile identities
```

Any mismatch makes the administration:

```text
V1A_QUALIFICATION_INVALID
```

only if the authority/administration defect is discovered after formal execution has begun. Before execution begins, an authority-guard failure is a blocked start, not a formal administration; its decision rule is specified in Section 43.

---

# 27. Evidence package

A valid first administration produces exactly the evidence needed for independent audit.

Required artifacts:

## 27.1 Qualification specification

The frozen Phase-13 specification.

## 27.2 Fixture manifest

Canonical fixture bytes and SHA-256s for:

```text
d0
dA
dB
```

and all exact observation-envelope construction parameters needed to reproduce the qualification.

## 27.3 Expected-result manifest

The preregistered machine-readable expectations and relations.

## 27.4 Identity binding record

Contains:

```text
repository commit
operator/projection identities
modulation identities
schema identities
Python version
platform
qualification harness identity/hash
manifest hashes
```

## 27.5 Run ledger

One ordered record for every:

```text
ingress attempt
lifecycle operation
recovery operation
pure-read stimulus
```

with success or exact typed failure outcome.

## 27.6 Receipt record

Canonical Phase-11 receipt sequence per qualification arm.

## 27.7 Projection record

Canonical nine-field Phase-5 projection sequence per qualification arm.

Each record is externally bound to its arm by the Phase-13 harness.

## 27.8 Durable-artifact hash ledger

SHA-256 values for canonical:

```text
configuration artifact
VHE sidecar artifact
```

at each preregistered commit/lifecycle checkpoint.

## 27.9 Restart/recovery ledger

For every E7 branch:

```text
pre-state hashes
fault injected
error type / field / reason / durable_committed
post-fault hashes
recovery action
post-recovery hashes
replay outcome
```

## 27.10 Phase-12 metrics record

Immutable final metrics for every Phase-12 host arm.

## 27.11 Final qualification result

Contains:

```text
administration identity
per-block E1–E12 verdicts
top-level taxonomy value
failure/invalidity sub-code if applicable
claim ceiling
```

No raw VHE state is included.

---

# 28. Independent audit sufficiency

The Phase-13 administration is considered fully specified only if an independent reviewer holding:

```text
frozen specification
fixture manifest
expected-result manifest
identity binding record
repository at recorded commit
```

can reproduce the run ledger, receipt records, canonical projection records, and durable-artifact hashes from the specified schedules.

If this is impossible because a schedule, fixture, identity, or fault condition is under-specified, the administration is:

```text
V1A_QUALIFICATION_INVALID
```

---

# 29. Formal first-administration protocol

Phase 13 uses one preregistered formal first administration.

Before execution, all of the following must already be committed/frozen:

```text
Phase-13 specification
Phase-13 qualification harness
fixture manifest
expected-result manifest
authority guard
clock schedules
lifecycle schedules
fault schedules
evidence schemas
exact execution command
```

No expected value may be changed after first execution begins.

No acceptance predicate may be added after observing a result.

No fixture may be changed.

No schedule may be altered.

No hidden retry is permitted.

---

# 30. Administration identity and no-retry rule

The first administration has a unique immutable administration identity derived from the frozen preregistration artifacts.

Once execution begins:

* a valid completed run yields PASS or FAIL;
* an invalid administration yields INVALID;
* the same administration identity is never silently rerun as though the first attempt did not happen.

If a new formal administration is later required after INVALID or after correcting an implementation defect, it requires:

```text
a new administration identity
preservation of prior evidence
explicit authorization
```

Any subsequent execution of the original frozen suite after a valid formal result is:

```text
REPRODUCTION / REGRESSION ONLY
```

Before execution begins, a failed preflight neither consumes the administration identity nor emits a PASS, FAIL, or INVALID taxonomy value.

---

# 31. Environmental validity

Environmental diagnostics outside E1–E12 do not automatically cause scientific failure.

Known unrelated examples may include:

```text
inaccessible .pytest_cache warning
Windows directory-symlink privilege error WinError 1314
```

However, if an environment limitation prevents any required E1–E12 branch from executing as preregistered, the formal administration is:

```text
V1A_QUALIFICATION_INVALID
```

with sub-code:

```text
INVALID_ENVIRONMENT
```

There is no PASS with an omitted required block.

An environment limitation discovered after a validly established required-block failure cannot convert that failure into `INVALID_ENVIRONMENT`. The top-level result remains `V1A_QUALIFICATION_FAIL` with the relevant failure sub-code, while the unexecuted branch is recorded as a coverage/environment gap. `V1A_QUALIFICATION_INVALID / INVALID_ENVIRONMENT` applies only when no required executed block has already established a valid FAIL and the environment prevents completion of the required matrix.

---

# 32. Top-level result taxonomy

Exactly three top-level outcomes exist:

```text
V1A_QUALIFICATION_PASS
V1A_QUALIFICATION_FAIL
V1A_QUALIFICATION_INVALID
```

There is no:

```text
PASS_WITH_LIMITATIONS
PARTIAL_PASS
CONDITIONAL_PASS
```

Qualification limitations belong in the claim ceiling.

---

# 33. FAIL taxonomy

A FAIL requires a sub-code.

## FAIL_SCIENTIFIC

A valid administration violates a preregistered scientific/product criterion whose authority belongs to a frozen scientific phase.

The correct response is governed scientific review of the phase owning that criterion.

It is not permission to tune Phase-13 expectations.

## FAIL_IMPLEMENTATION

The frozen scientific expectations remain authoritative, but assembled implementation behavior violates them.

Examples:

```text
unexpected exception
durability mismatch
determinism mismatch
replay duplicate
incorrect lifecycle continuation
nonzero projection-construction-failure metric
wrong canonical projection
wrong receipt
wrong artifact bytes
```

Correction may require implementation repair and a newly authorized administration.

A FAIL does not become PASS by rerunning until it succeeds.

If one valid administration establishes `FAIL_SCIENTIFIC` in one block and `FAIL_IMPLEMENTATION` in another, record every block's own failure classification. The top-level failure sub-code is `FAIL_SCIENTIFIC`, because it requires governed review of a frozen scientific criterion; the implementation failure remains in the block and result ledgers.

---

# 34. INVALID taxonomy

An INVALID result establishes nothing about whether v1a satisfies its criteria.

Required sub-codes include:

## INVALID_ADMINISTRATION

Examples:

```text
expected-result manifest not frozen first
wrong repository commit
dirty unauthorized worktree
fixture changed
schedule changed
theta arm mislabelled
raw VHE state entered evidence
acceptance predicate found in production Brainvision
evidence malformed or incomplete
hidden retry
```

## INVALID_ENVIRONMENT

A required E1–E12 branch cannot be executed because the environment does not satisfy its preregistered requirements.

The missing branch must be named explicitly.

---

# 35. PASS conditions

`V1A_QUALIFICATION_PASS` requires all of:

1. authority guard PASS;
2. administration validity PASS;
3. E1 PASS;
4. E2 PASS;
5. E3 PASS;
6. E4 PASS;
7. E5 reproduction PASS;
8. E6 PASS;
9. E7 PASS;
10. E8 PASS;
11. E9 PASS;
12. E10 PASS;
13. E11 PASS;
14. E12 PASS;
15. every Phase-12 `projection_construction_failures_total == 0`;
16. no raw-state evidence violation;
17. no unauthorized production integration;
18. complete auditable evidence package.

One failed or missing required block prevents PASS.

---

# 36. Phase-6 and Phase-7 handling

Phase 13 does not create a second formal Phase-6 or Phase-7 administration.

Any Phase-6/7 execution inside Phase 13 is classified:

```text
REPRODUCTION / REGRESSION ONLY
```

Phase-13 E1/E5 use prior frozen expected values as authority.

A mismatch is a qualification failure.

It is not a new estimate of the horizon or modulation effect.

---

# 37. Product-horizon interpretation

A PASS shows that the assembled system preserves the retained-history distinction at:

```text
300 active visual seconds after retained-event onset
```

under the frozen fixture.

This is a product-requirement floor.

It is not:

```text
a half-life
a measured decay constant
an upper memory bound
a measured expiry time
```

The frozen Persistent Context has no elapsed-time decay.

Therefore Phase 13 does not claim to discover a 300-second natural memory duration.

It shows that the assembled v1a product meets the required ≥300-active-second retained-history criterion.

---

# 38. Projection non-injectivity

Phase-13 observations occur through the bounded Phase-5 projection.

Projection is intentionally lossy and non-injective.

Therefore:

> Equality of projection fields means no observable divergence at the frozen projection resolution.

It does not establish raw internal state bit identity unless that identity is separately established by a frozen earlier-phase authority or by canonical durable artifact comparison authorized for that criterion.

No raw-state sink or qualification back-channel is added to compensate.

---

# 39. Degenerate current-activity control

In E1 and E2:

```text
current_activity_code = 0
```

because the terminal sampling descriptor is `d0` and therefore Fast Trace is canonically zero.

This exact prediction is preregistered.

The cross-arm equality is required by the frozen fixture, but Phase 13 explicitly does not present it as an independently informative matched-current experimental control.

The load-bearing history-sensitive criteria remain:

```text
E1 retained-history distinction
E2 trajectory distinction
```

---

# 40. Single-process claim boundary

Phase-12 same-lineage host uniqueness and delivery ordering are process-local.

Phase 13 must record that its formal qualification runs use the preregistered process model.

Unless a multiprocess administration is explicitly added before freeze, Phase-13 PASS does not establish cross-process sink-host serialization.

This does not weaken durable Phase-10 recovery semantics.

It limits only the Phase-12 process-local delivery claim.

---

# 41. Production-isolation gate

Before PASS, Phase 13 must statically and dynamically confirm that assembled qualification introduced no contact with:

```text
Fabric.ingest
MemoryGraph
memory formation
memory retrieval
memory kernel
CharacterSeed
CharacterState
CognitiveCore
SRG
Hivermind
Spine
prompt construction
model inference
LLM inference
```

Phase-13 test/evidence code itself must not route projection output into any of those systems.

---

# 42. Phase-13 implementation boundary

Phase 13 is expected to add only qualification/test/evidence machinery.

Preferred scope is conceptually:

```text
new:
tests/test_brainvision_phase13_v1a_qualification.py

new:
Phase-13 test-only qualification helpers

new:
machine-readable fixture/expected-result manifests

new:
Phase-13 qualification/evidence documentation
```

Expected modification to:

```text
brainvision/*.py
torment_service/*.py
```

is:

```text
0
```

If production behavior must change for Phase 13 to pass, stop.

---

# 43. Preflight before first administration

The formal administration must not begin until a deterministic preflight verifies:

```text
HEAD == expected frozen administration commit
origin/main == expected frozen administration commit
worktree clean
qualification specification hash correct
fixture manifest hash correct
expected-result manifest hash correct
authority identities correct
qualification harness hash correct
environment requirements satisfied
evidence output target empty/fresh
no prior run under same administration identity
```

Preflight failure prevents execution and results in no scientific verdict.

Before execution begins, if preflight detects a wrong HEAD, wrong `origin/main`, dirty unauthorized worktree, incorrect specification/manifest/harness hash, authority identity mismatch, non-fresh evidence directory, prior use of the same administration identity, or an environment incapable of beginning the frozen run:

```text
FORMAL ADMINISTRATION DOES NOT BEGIN
NO PASS / FAIL / INVALID TAXONOMY VALUE IS EMITTED
NO FORMAL RESULT DOCUMENT IS CREATED
ADMINISTRATION IDENTITY IS NOT CONSUMED
```

Correct the preflight problem and rerun preflight. This is a blocked start, not a scientific administration.

If an authority or administration defect is discovered only after formal execution has started, the administration is `V1A_QUALIFICATION_INVALID` with sub-code `INVALID_ADMINISTRATION`; the administration identity is consumed and prior evidence must be preserved.

---

# 44. Formal execution boundary

The exact command used for first administration must be frozen before execution.

The harness must expose no interactive tuning controls.

The run must:

```text
execute E1–E12
record all required evidence
compute each preregistered predicate
emit exactly one top-level taxonomy result
```

No result may depend on manual interpretation inserted during execution.

---

# 45. Result-document rules

A formal Phase-13 result document must include:

```text
administration identity
repository identity
manifest identities
environment identity
E1–E12 outcomes
top-level taxonomy result
failure/invalidity sub-code if applicable
evidence hashes
claim ceiling
```

If PASS, it must end with the HOLD block defined below.

If FAIL or INVALID, it must not claim qualification and must not emit the PASS HOLD block.

---

# 46. Claim ceiling for PASS

A Phase-13 PASS establishes only:

> The frozen deterministic TORMENT Brainvision v1a assembled product, under the preregistered synthetic fixtures and schedules, accepts typed firsthand visual observations through its direct ingress, advances Brainvision-owned active visual time, updates and durably preserves its frozen recursive state, reproduces its frozen character-modulation mapping, recovers from the enumerated persistence interruptions without duplicate application, enforces replay and identity boundaries, produces its frozen bounded relational projection at successful commits, and preserves diagnostic-sink isolation. Under the frozen retained-history fixture it exhibits a projection-visible retained-history distinction at least 300 active visual seconds after event onset. Under the frozen order fixture, exchanging the two non-neutral events reverses the sign of the single preregistered trajectory role (`+5` versus `-5`) while all five other Phase-5 projection roles remain equal. This establishes order-dependence of one antisymmetric relational coordinate on this frozen fixture; it does not establish general sensitivity to history order. The equal auxiliary `retained_history_code` values (`8` and `8`) are single-fixture reproduction data and do not establish that retained history is order-insensitive in general.

A PASS does **not** establish:

```text
emotion
attention
awareness
consciousness
experience
semantic understanding
memory formation
memory retrieval
MemoryGraph memory creation or retrieval
a natural 300-second memory duration
physical-world visual accuracy
general computer vision
arbitrary-camera behavior
arbitrary frame-rate invariance
LLM usefulness
model-output improvement
cognitive usefulness
v1b integration correctness
v1b readiness
cross-process Phase-12 sink serialization unless explicitly administered
universal cross-platform determinism unless explicitly administered
general order sensitivity beyond the frozen O1/O2 antisymmetric fixture
```

It does not establish that projection values have natural-language meaning.

It does not establish that projection can reconstruct raw VHE state.

Phase 13 does not re-establish that the public Phase-11 direct-ingress API is the only code path capable of mutating VHE state. Mutation-route exclusivity remains inherited frozen Phase-0 / Phase-11 architectural authority and is not a new Phase-13 assembled-product finding. Phase 12 contains a private Brainvision-owned committed-snapshot ingress seam used for lawful sink hosting; Phase 13 does not generalize from that implementation detail to a new exclusivity claim.

---

# 47. Inherited claim ceilings

The following earlier ceilings remain in force:

```text
retained_300_seconds_is_minimum_survival_not_half_life
s_has_no_elapsed_time_decay
w_has_no_claimed_nonzero_dead_zone_width
recurrence_is_register_window_relative
synthetic_qualification_does_not_prove_arbitrary_camera_behavior
no arbitrary frame-rate invariance
```

No Phase-13 wording may weaken them.

---

# 48. Mandatory post-PASS boundary

Only if the result is:

```text
V1A_QUALIFICATION_PASS
```

the final result document must terminate with:

```text
BRAINVISION_V1A:
QUALIFIED

MANDATORY_HOLD:
ACTIVE
```

Immediately beneath it:

> Phase 14 and beyond are NOT AUTHORIZED. This qualification authorizes no memory, cognitive, character, kernel, or model integration work, and no design, specification, prototyping, or implementation toward such integration. `MANDATORY_HOLD: ACTIVE` may be cleared only by an explicit, separately recorded authorization naming the specific scope released. Nothing in this result, and no absence of a finding in it, constitutes such authorization.

The PASS result contains no:

```text
next steps
future work
v1b readiness
integration roadmap
recommended consumer wiring
```

The HOLD is the terminal statement.

---

# 49. FAIL / INVALID terminal behavior

If result is:

```text
V1A_QUALIFICATION_FAIL
```

or:

```text
V1A_QUALIFICATION_INVALID
```

the result document ends with that result and its required sub-code/evidence.

It does not print:

```text
BRAINVISION_V1A: QUALIFIED
```

and does not activate the post-qualification HOLD block because qualification did not occur.

Further work requires an explicit response to the recorded failure or invalidity.

---

# 50. Pre-freeze requirements

Before this Phase-13 specification may be marked frozen:

1. Codex must review exact system fit and administration feasibility.
2. Claude must review scientific sufficiency and claim ceiling.
3. The retained-history appended-probe derivation must remain accepted.
4. The idempotent clock requirement must remain accepted.
5. E1–E12 must remain complete.
6. The expected-result-manifest schema must be reviewed.
7. Frozen pre-Phase-13 expected values, including auxiliary E2 retained-history predictions, must be resolved before first administration.
8. No production change may be required.
9. No earlier phase may require reopening.
10. The first-administration protocol must be accepted.

Required pre-freeze verdict:

```text
PHASE_13_SPECIFICATION_REVIEW:
PASS
```

---

# 51. Freeze transition

Only after final review may this document status change from:

```text
PRE-FREEZE CANDIDATE — FINAL v1a QUALIFICATION SPECIFICATION
```

to:

```text
FROZEN PRE-ADMINISTRATION PHASE-13 v1a QUALIFICATION SPECIFICATION
```

The exact freeze commit becomes the authority for Phase-13 harness construction and preregistration.

The qualification harness and expected-result manifest must themselves subsequently be frozen before formal first administration.

---

# 52. Final pre-administration state

The intended state immediately before first administration is:

```text
PHASE_13_SPECIFICATION:
FROZEN

PHASE_13_HARNESS:
FROZEN

PHASE_13_EXPECTED_RESULT_MANIFEST:
FROZEN

PHASE_13_AUTHORITY_GUARD:
PASS

FORMAL_FIRST_ADMINISTRATION:
AUTHORIZED / NOT RUN
```

No model, memory, cognitive, or v1b integration is authorized at this state.

---

# 53. Phase-13 design decision

This specification deliberately chooses:

```text
one bounded preregistered formal first administration
external grading
no production behavior changes
no raw-state evidence
no hidden retries
no Phase-6/7 re-administration
no partial PASS
terminal mandatory HOLD after PASS
```

The entire purpose of Phase 13 is to answer one final bounded question:

> Does the already-built Brainvision v1a system, exactly as frozen, satisfy its preregistered assembled-product contract?

Nothing beyond that question is authorized by this phase.
