# TORMENT Brainvision Phase 5 Projection and Quantization v1.0

## Status and boundary

This document freezes the bounded relational Phase-5 projection of the
Phase-4 A** VHE. It defines no recursive state, configuration, persistence,
lifecycle, Fabric registry, ingress, memory, cognition, kernel, SRG,
Hivermind, prompt, model, or Phase-7 modulation integration.

The projection is a pure read over a committed `VheState` and exact elapsed
active visual time. It evolves F only on an immutable as-of copy, derives the
projection, and never mutates supplied VHE state, R, a clock, persistence, or
any runtime subsystem. Repeated reads from the same state and elapsed time
produce byte-identical canonical projection bytes.

## Identity

```text
schema_id:    brainvision.projection.v1
algorithm_id: brainvision.projection.fixed16-relational.v1
manifest_core_sha256:
c9f5ed6b1300bc242d7633e6b0e7cea107e0473cfd26d9650abf8da9ad055b3f
projection_id:
bvproj1_c9f5ed6b1300bc242d7633e6b0e7cea107e0473cfd26d9650abf8da9ad055b3f
```

The manifest core binds the frozen Phase-4 operator ID,
`bvheop1_c367de696ba56b417054336a2ace5e8fd6b6b6a5cb3c7e3fa21f2bac4519d8bb`,
all field formulas/domains, quantization, role bindings, relevant field sets,
fixture expectations, canonical serialization, and claim ceiling. Canonical
ASCII core bytes are authoritative and never contain `projection_id`.
Object-form manifest views are fresh decoded copies.

## Exact quantization

```text
Q                   = 1_000_000
PROJECTION_STEPS    = 16
PROJECTION_QUANTUM  = 62_500 q
HALF_QUANTUM        = 31_250 q

unsigned_code(q) = RNE(16*q/Q), q in [0,Q],  output in [0,16]
signed_code(q)   = RNE(16*q/Q), q in [-Q,Q], output in [-16,16]
```

`RNE` is exactly the frozen Phase-4 signed quotient/remainder round-half-even
primitive. There is no float arithmetic, libm use, fitted threshold, or
alternative binning.

Unsigned code zero corresponds exactly to raw values `[0,31250]`; signed code
zero corresponds exactly to `[-31250,+31250]`. Numeric code zero therefore
means **quantized zero**, not necessarily raw zero.

The sixteen-step / 1/16 normalized full-scale grid is fixed before Phase 6.
Its rationale is a power-of-two interval count, exact divisibility of Q by 16,
exact 62,500-q spacing, 6.25% full-scale resolution, and a deliberately coarse
bounded summary without float or fitted thresholds.

For audit only, not as manifest authority:

| Steps | Retained separation | Order separation |
| ---: | ---: | ---: |
| 2 | 1 | 2 |
| 4 | 2 | 2 |
| 8 | 4 | 6 |
| 16 | 8 | 10 |
| 32 | 16 | 20 |
| 64 | 32 | 40 |

This demonstrates that 16 was not selected as the minimum grid satisfying the
retained-history requirement: four steps already reaches its two-code minimum.

## Canonical projection fields and roles

The canonical serialized DTO contains exactly:

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

It contains no raw F/S/R, W, c, timestamps, occurrence counts, descriptor
values, emotion labels, or Phase-7 modulation fields.

| Field | Exact source and encoding | Role |
| --- | --- | --- |
| `current_activity_code` | `unsigned_code(max(abs(f_eff_1_q), abs(f_eff_2_q)))`, where f_eff is from pure as-of evolved F | `CURRENT_ACTIVITY_ROLE` |
| `retained_history_code` | `unsigned_code(max(abs(S.luminance_q), abs(S.contrast_q), abs(S.orientation_q)))` | `RETAINED_HISTORY_ROLE` |
| `present_history_relation_code` | `signed_code(clamp(mul_q(f_eff_1_q,S.luminance_q) + mul_q(f_eff_2_q,S.contrast_q), -Q, Q))` | `PRESENT_HISTORY_RELATION_ROLE` |
| `trajectory_code` | `signed_code(S.orientation_q)` | `TRAJECTORY_ROLE` |
| `open_event_class` | `R.open_semantic_event_class`, a bounded Phase-2 token or null | `OPEN_EVENT_ROLE` |
| `recurrence_code` | 0 with no open token; 1 for open-token count 1; 2 for open-token count >=2 | `RECURRENCE_ROLE` |

`trajectory_code` is specifically the coarse signed A** orientation/order
context. It must not be described as convergence, divergence, stability, or
an objective trajectory.

The exact role bindings are one field each, in the table above.

## Relevant field sets and exact comparison

```text
retained current equality:   (current_activity_code,)
retained history difference: (retained_history_code,)
order current equality:      (current_activity_code,)
order history difference:    (trajectory_code,)
present/history relation:    (present_history_relation_code,)
open event:                  (open_event_class,)
recurrence:                  (recurrence_code,)
```

For a named relevant field set, `WITHIN_PROJECTION_QUANTUM` means exact
equality of every encoded canonical field in that set. Categorical, token, and
null values use exact equality. There is no tolerance, and this equality
relation is transitive.

## Frozen qualification fixtures

At the Phase-4 retained-history read:

```text
H0: current_activity_code = 0, retained_history_code = 0
H1: current_activity_code = 0, retained_history_code = 8
retained separation = 8; Phase-0 minimum = 2
```

For the frozen A** order states after final d0:

```text
O1: S.orientation_q = +320000, trajectory_code = +5
O2: S.orientation_q = -320000, trajectory_code = -5
trajectory separation = 10
```

The stale pre-A** `+/-400000` / `+/-6` result is not authoritative.

The frozen lawful present/history cases are:

| Case | Raw relation q | Code |
| --- | ---: | ---: |
| no current | 0 | 0 |
| aligned | +500000 | +8 |
| opposed | -187500 | -3 |
| orthogonal | 0 | 0 |

Open/recurrence qualification starts from the fresh/reset neutral VHE state
and uses only d0 semantic transitions. Under this frozen all-neutral fixture,
W is zero and F/S remain unchanged: fresh projects null/0; first
`detector:scene_change` projects that token/1; its recurrence projects the same
token/2; then `detector:motion` projects that token/1.

## Canonical serialization

Projection bytes are canonical ASCII JSON using:

```text
sort_keys=True
separators=(",", ":")
ensure_ascii=True
allow_nan=False
```

`open_event_class` is explicitly present as `null` when absent. Encoded numeric
values are exact integers.

## Claim ceiling and anti-tuning boundary

- The projection is a bounded summary, not raw VHE state.
- Current activity is quantized fast-trace activity, not an exact current image.
- Retained history is magnitude-only and loses coordinate identity/sign.
- Present/history relation is coarse coordinate alignment, not semantic interpretation.
- Trajectory is coarse signed A** orientation/order context.
- Open event is structural bookkeeping, not objective event truth.
- Recurrence is register-window-relative.
- Numeric zero means quantized zero, not raw zero; retained code zero can coexist
  with retained magnitude up to 31,250 q.
- Quantization discards sub-quantum differences. A one-code difference can arise
  from a bin boundary and alone has no special semantic significance.
- Synthetic qualification does not establish arbitrary camera/model understanding.
- Projection distinguishability does not establish downstream model usefulness.

After this freeze, Phase 6 may not rescue a failure by changing the step count,
quantum, bins, signed/unsigned binding, source formulas, role bindings,
relevant field sets, or special cases. Such a change requires a new projection
identity and renewed authorization.
