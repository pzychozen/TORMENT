# TORMENT Brainvision Production — Phase 13 Formal Administration Bindings v1.0

## Status

    FROZEN PHASE-13 FORMAL ADMINISTRATION BINDINGS — PREREGISTRATION AUTHORITY

## Authority and scope

This addendum is subordinate to docs/TORMENT_BRAINVISION_PHASE_13_COMPLETE_V1A_QUALIFICATION_SPECIFICATION_v1.0.md. It narrows only previously unspecified administration details. It does not alter an E1–E12 scientific criterion, production behavior, an expected scientific outcome, a threshold, or a claim ceiling.

## 1. Global deterministic administration bindings

    workspace_id = "bv13-qualification"

Use one deterministic agent per formal arm. Agent IDs are the exact lowercase hyphenated arm IDs specified below and must satisfy the existing repository/path/Phase-2 identifier rules.

Unless an arm explicitly overrides a value, observations use:

    stream_identity = block-specific value defined below
    adapter_id = "bv13-adapter-a"
    adapter_contract_id = "bv13-contract-a"

    source_capture_time_unix_ns = null
    confidence_q = null
    semantic_event_class = null
    world_event_id = null

Default Brainvision modulation is theta = 0, except where E5 specifies another value. Every fresh lineage begins with:

    last_accepted_source_sequence = -1

No random UUID, random token, wall-clock-derived name, or generated identifier is permitted in the formal administration.

No other formal agent may be created unless separately preregistered. The later schedule manifest must match this addendum exactly; deterministic test-only IDs must not be silently translated.

## 2. Standard qualification observation sequence

STANDARD_THREE_EVENT_SEQUENCE means exactly:

    seq 0: d0 @ active time 0 ns
    seq 1: dA @ active time 1_000_000_000 ns
    seq 2: d0 @ active time 2_000_000_000 ns

All default metadata applies unless an arm explicitly overrides it. Observation IDs are derived only by the frozen Phase-2 canonical identity rule and are never manually selected.

## 3. E1 bindings

    stream_identity = "bv13-e1-stream"
    adapter_contract_id = "bv13-contract-a"
    theta = 0
    sink = recording

    E1_H0 -> agent_id = "e1-h0"
      seq 0 d0 @ 0
      seq 1 d0 @ 1_000_000_000
      seq 2 d0 @ 2_000_000_000
      seq 3 d0 @ 301_000_000_000

    E1_H1 -> agent_id = "e1-h1"
      seq 0 d0 @ 0
      seq 1 dA @ 1_000_000_000
      seq 2 d0 @ 2_000_000_000
      seq 3 d0 @ 301_000_000_000

No further E1 administration choice remains.

## 4. E2 bindings

    stream_identity = "bv13-e2-stream"
    theta = 0
    sink = recording
    source_sequence = 0, 1, 2, 3
    active_time = 0, 1 s, 2 s, 3 s

    E2_O1 -> agent_id = "e2-o1"
      d0, dA, dB, d0

    E2_O2 -> agent_id = "e2-o2"
      d0, dB, dA, d0

Frozen auxiliary reproduction is retained_history_code: O1 = 8, O2 = 8. The sole order-sensitive acceptance field is trajectory_code: O1 = +5, O2 = -5.

## 5. E3 — metadata inertness bindings

All direct metadata twin administrations use:

    stream_identity = "bv13-e3-stream"
    theta = 0
    sink = recording
    seq 0 d0 @ 0
    seq 1 dA @ 1_000_000_000
    seq 2 d0 @ 2_000_000_000

Only the named field of seq 1 / dA differs between paired arms unless stated otherwise. All other observation fields remain identical.

### E3.1 adapter ID twin

    agents: "e3-adapter-a", "e3-adapter-b"
    seq 1, arm A: adapter_id = "bv13-adapter-a"
    seq 1, arm B: adapter_id = "bv13-adapter-b"
    seq 0 and seq 2 in both arms: adapter_id = "bv13-adapter-a"

### E3.2 capture-time twin

    agents: "e3-capture-a", "e3-capture-b"
    seq 1, arm A: source_capture_time_unix_ns = 111_111_111
    seq 1, arm B: source_capture_time_unix_ns = 222_222_222
    seq 0 and seq 2: source_capture_time_unix_ns = null

### E3.3 confidence twin

    agents: "e3-confidence-a", "e3-confidence-b"
    INERTNESS TWIN VALUES
    seq 1, arm A: confidence_q = 250_000
    seq 1, arm B: confidence_q = 750_000
    seq 0 and seq 2: confidence_q = null

### E3.4 world-event twin

    agents: "e3-world-a", "e3-world-b"
    seq 1, arm A: world_event_id = "world-a"
    seq 1, arm B: world_event_id = "world-b"
    seq 0 and seq 2: world_event_id = null

### E3.5 source-sequence / observation-ID offset twin

    agents: "e3-sequence-base", "e3-sequence-offset"
    descriptors and active time in both arms: d0 @ 0, dA @ 1 s, d0 @ 2 s
    base source sequences: 0, 1, 2
    offset source sequences: 100, 101, 102

Observation IDs are canonically derived from each arm's own source sequences. The normative comparison is: Phase-5 canonical projection bytes equal. Receipt IDs/sequences and configuration/sidecar watermark fields are intentionally different. Complete durable-artifact byte equality is not required.

### E3.6 adapter-contract twin

    agents: "e3-contract-a", "e3-contract-b"
    stream_identity = "bv13-e3-contract-stream"

    arm A configuration and every observation: adapter_contract_id = "bv13-contract-a"
    arm B configuration and every observation: adapter_contract_id = "bv13-contract-b"

    both descriptor, sequence, and active-time schedules:
      d0 seq 0 @ 0
      dA seq 1 @ 1 s
      d0 seq 2 @ 2 s

The normative comparison is: Phase-5 canonical projection bytes equal. Configuration/sidecar byte equality is not required because contract identity is intentionally different.

### E3.7 forged observation identity

    agent_id = "e3-invalid-id"
    stream_identity = "bv13-e3-invalid-stream"
    accept seq 0 d0 @ 0
    set clock = 1 s
    construct a lawful exact-type FirsthandVisualObservationV1 for seq 1 dA
    with derive_observation_id(stream_identity, 1)
    TEST_ONLY_DTO_IDENTITY_TAMPER:
      object.__setattr__(
          observation,
          "observation_id",
          derive_observation_id(observation.stream_identity, 2),
      )
    attempt tampered seq 1 (source_sequence remains 1)
    construct a fresh lawful canonical seq 1 dA normally
    attempt canonical seq 1 again at the same harness-set clock

Only the already-validated instance's observation_id changes; no other field changes. The first seq 1 attempt is the frozen Phase-11 ingress branch with field = "observation_id" and reason = "invalid_observation_id". Because source_sequence 1 is greater than watermark 0, replay does not mask the identity guard. The Phase-2 constructor error mismatched_stream_sequence_identity is not graded. The fresh canonical second attempt proves no residue from refusal.

TEST_ONLY_DTO_IDENTITY_TAMPER is not an E7 persistence fault and is not added to the three formal E7 fault IDs.

## 6. E4 — semantic isolation bindings

    E4_NULL  -> agent_id = "e4-null"
    E4_EVENT -> agent_id = "e4-event"

    stream_identity = "bv13-e4-stream"
    adapter_contract_id = "bv13-contract-a"
    theta = 0
    sink = recording
    seq 0 d0 @ 0
    seq 1 dA @ 1_000_000_000

    E4_NULL:  seq 0 semantic_event_class = null; seq 1 semantic_event_class = null
    E4_EVENT: seq 0 semantic_event_class = null; seq 1 semantic_event_class = "phase13:event-a"

No other field differs. phase13:event-a is the only semantic token used in formal E4. E4 grading remains limited to the frozen sink-visible projection claims.

At the seq 1 commit, both arms reproduce:

    current_activity_code = 16
    retained_history_code = 8
    present_history_relation_code = 8
    trajectory_code = 0

The R-derived projections are:

    E4_NULL:
      open_event_class = null
      recurrence_code = 0

    E4_EVENT:
      open_event_class = "phase13:event-a"
      recurrence_code = 1

The load-bearing E4 criterion remains that the four dynamical projection fields are equal across the two arms while only the frozen R-derived fields differ as preregistered. These exact values are reproduction predictions from frozen Phase-4/5 behavior, not new thresholds.

dA is used at the semantic divergence point so semantic-isolation equality is exercised while Fast Trace/Persistent Context dynamics are non-trivial. This prevents the criterion from passing merely because an all-d0 trajectory keeps every dynamical field at zero. This changes stimulus power, not the scientific criterion.

## 7. E5 bindings

    agents: "e5-theta-neg1", "e5-theta-zero", "e5-theta-pos1"
    stream_identity = "bv13-e5-stream"
    adapter_contract_id = "bv13-contract-a"
    sink = recording

    e5-theta-neg1 -> theta = -1
    e5-theta-zero -> theta = 0
    e5-theta-pos1 -> theta = +1

    all arms:
      d0 seq 0 @ 0
      dA seq 1 @ 1 s
      d0 seq 2 @ 2 s
      d0 seq 3 @ 301 s

No E5 lineage or schedule choice remains runtime-selectable.

The parent Phase-13 specification records corresponding H0 predictions current_activity_code = 0 and retained_history_code = 0. Phase 13 does not administer three additional all-neutral E5 arms. Those H0 values are AUTHORITY_ONLY_STRUCTURAL_REPRODUCTION_REFERENCE, inherited from frozen Phase-7 domain-wide H0 authority and the frozen all-d0 neutral trajectory. They are not separate Phase-13 E5 administered criteria.

The later expected-result manifest must distinguish:

    E5 administered criteria:
      three H1 theta arms -> retained 6 / 8 / 10

    E5 authority-only references:
      H0 current = 0
      H0 retained = 0
      theta = -1 / 0 / +1

The grader must never require nonexistent H0 E5 evidence records. Three additional all-neutral arms would reproduce a structural consequence already frozen by Phase 7 and add no information about the assembled configuration-to-theta-to-dynamics binding that E5 qualifies. This does not weaken the E5 H1 criterion.

## 8. E6 — restart/reload bindings

    E6_CONTROL -> agent_id = "e6-control"
    E6_RESTART -> agent_id = "e6-restart"
    stream_identity = "bv13-e6-stream"

    k = source_sequence 1
    k+1 = source_sequence 2
    DELTA_DOWN_NS = 10_000_000_000
    DELTA_ACTIVE_NS = 1_000_000_000

Both begin with seq 0 d0 @ committed active time 0 and seq 1 dA @ committed active time 1_000_000_000.

    E6_CONTROL:
      clock 0  -> admit seq 0 d0
      clock 1s -> admit seq 1 dA
      clock 2s -> admit seq 2 d0
      expected seq 2 committed active time = 2_000_000_000

    E6_RESTART:
      clock 0  -> admit seq 0 d0
      clock 1s -> admit seq 1 dA
      close host
      destroy manager
      advance source 1s -> 11s
      rebuild manager at source 11s
      create replacement recording host
      advance source 11s -> 12s
      admit seq 2 d0
      expected seq 2 committed active time = 2_000_000_000

The 10-second external downtime is excluded. No other E6 observation is permitted.

DELTA_DOWN_NS = 10_000_000_000 is a single nonzero downtime witness. Its value being greater than the frozen 5-second Fast Trace horizon improves detectability of an erroneous downtime-inclusion implementation; it does not create a 10-second product or retention claim.

## 9. E7 global bindings

Every E7 branch uses an independent agent lineage with theta = 0 and adapter_contract_id = "bv13-contract-a".

    E7.1 stream = "bv13-e7-1-stream"
    E7.2 stream = "bv13-e7-2-stream"
    E7.3 stream = "bv13-e7-3-stream"
    E7.4 control stream = "bv13-e7-4-control-stream"
    E7.4 fault stream = "bv13-e7-4-fault-stream"
    E7.5 stream = "bv13-e7-5-stream"

### E7.1 sidecar-write failure

    agent_id = "e7-1-sidecar-failure"
    seq 0 d0 @ 0 -> accepted
    set clock = 1 s
    install E7_SIDECAR_WRITE_FAIL
    attempt seq 1 dA
    capture failure/artifacts
    clear fault
    retry the exact same canonical seq 1 dA at unchanged clock = 1 s

The retry is part of the frozen branch and must succeed if the earlier failure produced no durable acceptance.

### E7.2 configuration-write-before-durability failure

    agent_id = "e7-2-config-failure"
    seq 0 d0 @ 0 -> accepted
    set clock = 1 s
    install E7_CONFIG_WRITE_PRE_DURABILITY_FAIL
    attempt seq 1 dA
    capture recovery_required failure and artifacts
    clear fault
    close host
    destroy manager
    rebuild manager at unchanged clock = 1 s
    trigger recovery access
    capture repaired artifacts
    attempt replay of seq 1 dA at unchanged clock = 1 s
    set clock = 2 s
    admit seq 2 d0

The replay must be refused.

### E7.3 isolated SIDECAR_AHEAD recovery

    agent_id = "e7-3-sidecar-ahead"
    seq 0 d0 @ 0 -> accepted
    set clock = 1 s
    install E7_CONFIG_WRITE_PRE_DURABILITY_FAIL
    attempt seq 1 dA

This produces the preregistered durable pair:

    configuration watermark = 0
    sidecar accepted_source_sequence = 1
    relation = SIDECAR_AHEAD

Then:

    clear fault
    close host
    destroy manager
    rebuild manager at unchanged clock = 1 s
    capture pre-recovery durable artifacts
    perform one runtime_snapshot stimulus and discard return
    capture post-first-access artifacts
    perform a second runtime_snapshot stimulus and discard return
    capture post-second-access artifacts

The first access performs exactly one watermark repair and the second performs no additional repair. The setup must not construct or inject raw VHE values manually.

### E7.4 both writes durable before runtime adoption

    agents: "e7-4-control", "e7-4-fault"

    both schedules:
      seq 0 d0 @ 0
      seq 1 dA @ 1 s
      seq 2 d0 @ 2 s

    control: no fault

    fault arm before seq 1:
      install E7_CONFIG_WRITE_POST_DURABILITY_RAISE
      attempt seq 1 at 1 s
      capture typed failure and durable artifacts
      clear fault
      close host
      destroy manager
      rebuild manager at unchanged source value 1 s
      perform recovery-triggering access
      capture artifacts proving no repair
      attempt replay seq 1 at 1 s
      set clock = 2 s
      admit seq 2 d0

The replay must be refused. The seq 2 continuation is compared with control.

### E7.5 post-commit delivery failure

    agent_id = "e7-5-throwing-sink"
    stream_identity = "bv13-e7-5-stream"
    sink = throwing
    seq 0 dA @ 0

    after admit:
      capture returned receipt
      capture metrics
      capture durable artifacts
      close throwing host
      create replacement recording host
      attempt replay of canonical seq 0 dA at unchanged clock = 0

Expected throwing-host metrics are:

    sink_invocations_total = 0
    sink_delivery_failures_total = 1
    projection_construction_failures_total = 0

No second successful observation is required.

dA is used so the durably committed E7.5 observation produces a non-trivial state and a sidecar whose content would be sensitive to duplicate application. E7.5 itself does not perform a later projection-level comparison and therefore does not independently establish projection-visible duplicate detection. Within E7.5, duplicate reapplication is structurally prevented by the durable watermark and is verified by the refused replay through the replacement host. Projection-level duplicate-update detection is exercised separately by the E7.2 and E7.4 continuation comparisons. The use of dA strengthens the branch's committed-state sensitivity without adding a new E7.5 criterion.

## 10. E8 replay bindings

Each branch uses a fresh independent lineage and the block stream identity "bv13-e8-stream".

    E8.1 agent_id = "e8-equal"
      seq 0 d0 @ 0 -> accepted
      attempt canonical seq 0 d0 again at unchanged clock = 0
      set clock = 1 s
      admit lawful seq 1 dA

    E8.2 agent_id = "e8-below"
      seq 0 d0 @ 0
      seq 1 dA @ 1 s
      attempt canonical seq 0 d0 at unchanged clock = 1 s
      set clock = 2 s
      admit seq 2 d0

    E8.3 agent_id = "e8-reload"
      seq 0 d0 @ 0
      close host
      destroy manager
      rebuild manager at unchanged clock = 0
      create replacement host
      attempt replay seq 0 d0 @ 0
      set clock = 1 s
      admit seq 1 dA

    E8.4 agent_id = "e8-recovered"
      seq 0 d0 @ 0
      set clock = 1 s
      install E7_CONFIG_WRITE_PRE_DURABILITY_FAIL
      attempt seq 1 dA
      clear fault
      close host and destroy manager
      rebuild at unchanged clock = 1 s
      trigger recovery
      attempt replay seq 1 dA at 1 s
      set clock = 2 s
      admit seq 2 d0

    E8.5 agent_id = "e8-invalid-id"
      seq 0 d0 @ 0 -> accepted
      set clock = 1 s
      construct a lawful exact-type seq 1 dA with derive_observation_id(stream, 1)
      TEST_ONLY_DTO_IDENTITY_TAMPER replaces only observation_id with
      derive_observation_id(observation.stream_identity, 2)
      attempt tampered seq 1 (source_sequence remains 1)
      submit canonical seq 1 dA at unchanged clock = 1 s

The tampered E8.5 attempt must surface the existing Phase-11 ingress failure field = "observation_id", reason = "invalid_observation_id"; it does not grade the Phase-2 constructor error. The fresh canonical second attempt proves no residue from ID refusal. E8.3 makes no downtime claim; E6 owns downtime qualification.

## 11. E9 bindings

    agents: "e9-read-0", "e9-read-1", "e9-read-7", "e9-repair"
    stream_identity = "bv13-e9-stream"

e9-read-0, e9-read-1, and e9-read-7 use STANDARD_THREE_EVENT_SEQUENCE with a recording sink. Between seq 1 and seq 2, at exactly 1_500_000_000 ns, they perform respectively 0, 1, or 7 runtime_snapshot() stimuli. The clock remains exactly 1_500_000_000 ns for every repeated stimulus. They then set 2_000_000_000 ns and admit seq 2.

e9-repair uses the E7.3 SIDECAR_AHEAD setup: seq 0 d0 @ 0, then seq 1 dA attempted at 1 s under E7_CONFIG_WRITE_PRE_DURABILITY_FAIL. It rebuilds at clock 1 s and performs:

    runtime_snapshot stimulus #1
    artifact checkpoint
    runtime_snapshot stimulus #2
    artifact checkpoint

No raw snapshot return is retained.

{0,1,7} snapshot stimuli are finite witnesses of the frozen structural read-purity property, not a sampled frequency range. The 1.5 s stimulus point lies inside the active Fast Trace window so the discarded pure read performs non-trivial as-of evolution while the idempotent clock prevents read count from changing time.

## 12. E10 lifecycle bindings

    agent_id = "e10-lifecycle"
    stream_identity = "bv13-e10-stream"
    sink = recording

    clock 0:
      configure theta 0
      enable
      admit seq 0 d0

    suspend at external clock 0
    advance harness clock by 10_000_000_000 ns while suspended
    attempt seq 1 dA while suspended -> refusal
    resume at external clock 10 s
    advance harness clock by 1_000_000_000 ns to 11 s
    admit seq 1 dA

The expected committed active time of seq 1 is 1_000_000_000. At unchanged external clock 11 s, reset while active. Reset establishes committed active time 0 while the watermark remains 1.

    attempt replay seq 1 dA -> refusal
    disable
    capture sidecar absence
    attempt seq 2 d0 while disabled -> refusal
    re-enable at unchanged external clock 11 s
    advance harness clock by 1_000_000_000 ns to 12 s
    admit seq 2 d0

After re-enable seq 2, expected committed active time is 1_000_000_000 and watermark is 2. This is the only formal E10 lifecycle sequence.

DELTA_SUSP_NS = 10_000_000_000 is one nonzero suspension witness, not a claim over arbitrary suspension duration.

## 13. E11 sink-purity bindings

    agents: "e11-null", "e11-recording", "e11-throwing"
    stream_identity = "bv13-e11-stream"
    N = 2
    ADMINISTERED_SINK_PURITY_DEPTH = 2

    initial compared segment:
      seq 0 d0 @ 0
      seq 1 dA @ 1 s

    E11_NULL -> sink = None
    E11_RECORDING -> sink = recording
    E11_THROWING -> sink = throwing

Capture receipts, durable artifacts at seq 0 and seq 1, and initial-host metrics. Expected initial-host metrics are:

    null:      0, 0, 0
    recording: sink_invocations_total = 2
               sink_delivery_failures_total = 0
               projection_construction_failures_total = 0
    throwing:  sink_invocations_total = 0
               sink_delivery_failures_total = 2
               projection_construction_failures_total = 0

For all three arms:

    close initial host
    create a replacement recording host on the same lineage
    set clock = 2_000_000_000
    admit seq 2 d0
    capture seq 2 projection and durable artifacts

The seq 2 recording is the future-projection purity comparison point. No further E11 observations occur.

No arbitrary-length sink-purity claim follows from the administered depth of 2.

## 14. E12 whole-run determinism binding

    agents: "e12-repeat-a", "e12-repeat-b"
    stream_identity = "bv13-e12-stream"
    adapter_contract_id = "bv13-contract-a"
    theta = 0
    sink = recording

    clock 0:
      enable
      admit seq 0 d0
    clock 1 s:
      admit seq 1 dA
    clock remains 1 s:
      attempt replay of seq 1 dA
    clock 2 s:
      admit seq 2 d0

No other lifecycle operation, restart, sink substitution, or fault occurs. The two entire bounded runs are compared as specified by E12. This is the complete formal E12 schedule.

## 15. Common stream bindings and sink rule

    E6  stream = "bv13-e6-stream"
    E8  stream = "bv13-e8-stream"
    E9  stream = "bv13-e9-stream"
    E10 stream = "bv13-e10-stream"
    E11 stream = "bv13-e11-stream"
    E12 stream = "bv13-e12-stream"

Independent lineages within a block may share the block stream identity. E7 uses its explicitly branch-specific streams. Unless an arm explicitly specifies sink = None or sink = throwing, its host uses a recording sink. No other sink mode exists in the formal administration.

## 16. Formal fault and checkpoint bindings

The only formal fault IDs are:

    E7_SIDECAR_WRITE_FAIL
    E7_CONFIG_WRITE_PRE_DURABILITY_FAIL
    E7_CONFIG_WRITE_POST_DURABILITY_RAISE

E7.3 and E8.4 use E7_CONFIG_WRITE_PRE_DURABILITY_FAIL; no fourth hidden fault exists.

No aliases are permitted. The existing untracked backend's legacy fault names will be removed after this addendum is frozen.

Checkpoint IDs may be mechanically derived as:

    <block>-<arm>-<operation-index>-<kind>

where kind is one of:

    configuration
    sidecar
    metrics
    receipt
    projection
    recovery

Checkpoint labels are not scientific administration choices; their schedule positions are.

## 17. Expected-manifest consequence and scientific scope

The later expected-result manifest must bind these administration values exactly. It may not change a descriptor sequence, source sequence, metadata value, semantic token, restart observation, E11 N, E12 schedule, or fault. Expected outcomes remain governed by the frozen Phase-13 specification. These bindings freeze stimuli, not new scientific thresholds.

They make every already-frozen E1–E12 criterion executable, isolate the named variable, use the smallest deterministic schedule exercising that property, and add no scientific hypothesis. They create no E13, projection role, theta value, fixture, acceptance threshold, or claim ceiling.

## 18. Review-before-instrument rule

Do not update schedule_manifest.json or complete grader.py until this addendum completes scientific/system review.

MACHINE_EXECUTABLE_E1_E12_SCHEDULES:
BLOCKED_PENDING_BINDINGS_FREEZE

INDEPENDENT_E1_E12_GRADER:
BLOCKED_PENDING_BINDINGS_FREEZE

    FORMAL_AUTHORIZATION_LATCH:
    CLOSED

    FORMAL_E1_E12_ADMINISTRATION_RUNS:
    0
