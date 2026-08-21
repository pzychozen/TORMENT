# TORMENT Brainvision Phase 6 Horizon Acceptance v1.0

## Status and scope

This document preregisters the deterministic Phase-6 synthetic qualification
matrix. It adds no production runtime functionality. The authoritative
machine-readable matrix is
`tests/fixtures/brainvision_phase6_horizon_acceptance_manifest.json`.

Phase 6 consumes the frozen Phase-2 fixtures, Phase-4 operator, and Phase-5
projection without changing descriptors, timing, operator equations,
projection fields, quantization, relevant field sets, or thresholds. Phase 7
is prohibited until Phase 6 is recorded complete.

## Frozen authorities

```text
Phase-4 operator_id:
bvheop1_c367de696ba56b417054336a2ace5e8fd6b6b6a5cb3c7e3fa21f2bac4519d8bb

Phase-5 projection_id:
bvproj1_c9f5ed6b1300bc242d7633e6b0e7cea107e0473cfd26d9650abf8da9ad055b3f

T_PRODUCT_V1:
300 active visual seconds
```

## Classification

- **Administration guard:** authorities/matrix bindings.
- **Primary formal acceptance:** retained horizon.
- **Mandatory qualification:** order, open event/recurrence, neutral/reset d0,
  world-event metadata invariance, semantic/dynamical isolation, pure-read
  determinism, and deterministic reconstruction.
- **Supporting coverage:** present/history relation.

The administration guard verifies that the committed administration still
matches the frozen Phase-2/4/5 authorities. It is not primary acceptance,
mandatory scientific qualification, or supporting scientific coverage.

The primary retained-horizon test alone has the frozen formal failure verdict
`VHE_ACCEPTANCE_FAIL`. A mandatory-qualification failure blocks Phase-6
completion; no additional failure-label vocabulary is introduced here.

## Primary retained-horizon matrix

```text
H0: d0 at t=0s, d0 at t=1s, d0 at t=2s
H1: d0 at t=0s, dA at t=1s, d0 at t=2s

pure read target: t=301s active visual time
elapsed after final event: 299s
elapsed after dA onset: 300s

current equality fields:   (current_activity_code,)
retained difference fields:(retained_history_code,)

H0: current_activity_code=0, retained_history_code=0
H1: current_activity_code=0, retained_history_code=8
expected separation: 8
minimum separation: 2
```

Primary PASS requires exact encoded current equality, retained distinction,
absolute retained-code separation of at least two, and the preregistered 0/8
values. Any primary failure is `VHE_ACCEPTANCE_FAIL`.

## Mandatory order qualification

```text
O1: d0,dA,dB,d0 at t=0,1,2,3s
O2: d0,dB,dA,d0 at t=0,1,2,3s

current equality fields: (current_activity_code,)
history difference fields: (trajectory_code,)

O1: current_activity_code=0, trajectory_code=+5
O2: current_activity_code=0, trajectory_code=-5
expected trajectory separation: 10
```

PASS requires exact current equality, trajectory distinction, and exact +5/-5
values. This is the Phase-0 required non-semantic order-sensitive subtest.

## Supporting present/history relation coverage

The relation field set is `(present_history_relation_code,)`. The frozen cases
are no-current `0/0`, aligned `+500000/+8`, opposed `-187500/-3`, and
orthogonal `0/0`, where each pair is raw relation q/code. These cases provide
role coverage only and do not introduce another baseline acceptance verdict.

## Mandatory event, neutral, and invariance qualifications

Open-event/recurrence begins from fresh/reset neutral VHE and uses d0-only
semantic observations. The expected projection sequence is:

```text
fresh:                       null, 0
first detector:scene_change: detector:scene_change, 1
repeat detector:scene_change:detector:scene_change, 2
new detector:motion:         detector:motion, 1
```

Under this frozen all-neutral fixture, W is zero and F/S remain unchanged.

The remaining mandatory checks assert:

- continued d0 from fresh/reset neutral state has the frozen no-write/no-change behavior;
- histories differing only in `world_event_id` leave F/S/W and dynamical
  projection fields bit-identical;
- semantic-class-only variation leaves F/S/W bit-identical while R may differ;
- pure reads do not mutate committed VHE and repeated reads yield identical
  canonical projection bytes; and
- reconstructing the frozen synthetic histories twice yields identical states
  and canonical projection bytes.

No blanket camera-frame-rate-invariance test or claim belongs in Phase 6.

## Exact comparison and anti-tuning

`WITHIN_PROJECTION_QUANTUM` means exact equality of every canonical encoded
value in the preregistered relevant field set. There is no tolerance.

The administration must not alter fixture descriptors, active-time schedules,
operator/projection identity, projection steps, quantizer, field bindings,
relevant field sets, or the minimum retained separation. Any such change
requires the governing new identity and renewed authorization.

## Administration doctrine

Phase-1-5 unit and regression tests are freely rerunnable verification.
Phase-6 scientific acceptance is one recorded first administration after this
preregistration is committed. Later Phase-6 runs are reproduction or
verification only and do not replace that first recorded result. The matrix is
deterministic local computation; no stochastic retry doctrine applies.

## Claim ceiling

A Phase-6 pass establishes only that the frozen deterministic synthetic
Brainvision operator/projection satisfies this preregistered v1a qualification
matrix at the frozen product horizon. It does not establish arbitrary camera or
semantic visual understanding, downstream LLM usefulness, physical-world
vision accuracy, universal frame-rate invariance, Phase-7 modulation validity,
lifecycle/persistence correctness, or full Brainvision product readiness.
