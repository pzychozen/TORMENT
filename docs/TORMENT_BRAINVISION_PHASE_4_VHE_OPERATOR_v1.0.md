# TORMENT Brainvision Phase 4 VHE Operator v1.0

## Status

This document freezes `fixedpoint-context-a-double-star.v1`, the isolated
fixed-point visual-history operator. It defines no projection, modulation,
configuration, persistence, lifecycle, ingress, Fabric, memory, cognition,
kernel, SRG, Hivermind, or model integration.

## Exact representation

```text
Q                                   = 1_000_000
FAST_HORIZON_NS                     = 5_000_000_000
CONTEXT_BLEND_Q                     = 500_000
R_CAPACITY                          = 8
RETAINED_HISTORY_INTERNAL_MARGIN_Q  = 500_000
ORDER_ORIENTATION_INTERNAL_MARGIN_Q = 500_000
```

All operator arithmetic is exact Python integer arithmetic. There is no float
arithmetic and no libm use. The operator receives exact elapsed active visual
nanoseconds from its caller; it does not call `clock.py` or
`time.monotonic_ns()`.

## Input normalization

For the frozen descriptor coordinate order:

```text
u1 = clamp(4 * (mean_luminance_q - 500000), -Q, Q)
u2 = clamp(4 * mean_adjacent_luminance_difference_q, 0, Q)
```

Therefore `d0 -> (0,0)`, `dA -> (Q,0)`, and `dB -> (0,Q)`.

## Signed round-half-even

`RNE(numerator / positive_denominator)` uses the exact signed
quotient/remainder procedure:

```text
sign = -1 if numerator < 0 else +1
q, r = divmod(abs(numerator), denominator)

if 2*r > denominator:
    q += 1
elif 2*r == denominator and q is odd:
    q += 1

return sign*q
```

`mul_q(a,b)` is exactly one `RNE(a*b/Q)` operation on the full integer product.
It does not use truncation, floor division semantics, or `round()`.

## State

```text
F = (amplitude_1_q, amplitude_2_q, remaining_ns)
S = (luminance_q, contrast_q, orientation_q)
R = bounded semantic register
```

F bounds are `[-Q,Q] x [0,Q] x [0,FAST_HORIZON_NS]`. Its canonical invariant
is `remaining_ns == 0` if and only if both amplitudes are zero. S is bounded in
the invariant cube `[-Q,Q]^3` and does not decay with elapsed active time.
VHE state has no active-time epoch.

R holds at most eight lexicographically ascending entries, each containing an
opaque semantic token, first/last active-time timestamps, and a saturating
count in `1..2^63-1`. Its separate open-token field is null exactly when R is
empty; otherwise it names an existing entry. It is the most recently admitted
non-null token, not a claim that an objective real-world event continues.

## Free evolution

For exact non-negative elapsed `delta_ns`:

```text
remaining' = max(0, remaining_ns - delta_ns)

if remaining' == 0:
    F' = (0,0,0)
else:
    F' = (amplitude_1_q, amplitude_2_q, remaining')
```

After evolution, using the EVOLVED/CANONICALIZED `remaining_ns` above (never
the pre-evolution duration):

```text
f_eff_i = RNE(amplitude_i_q * remaining_ns / FAST_HORIZON_NS)
```

S and R are unchanged by free elapsed time. This integer evolution satisfies
`E(a, E(b, F)) == E(a+b, F)` exactly for non-negative integer nanosecond
deltas. Pure as-of evaluation returns a new immutable state and does not
mutate committed state.

## Observation update

The update receives state, a `LowLevelVisualDescriptorV1`, optional opaque
semantic token, `prior_committed_active_time_ns`, and
`elapsed_active_time_ns`. Its event time is their exact integer sum.

The update order is frozen:

1. evolve F;
2. canonicalize expired F;
3. derive `f_eff`;
4. derive `u`;
5. derive W;
6. derive raw and clamped c;
7. derive gains;
8. update S;
9. overwrite/canonicalize F from current u;
10. update R.

```text
W = min(Q, abs(u1) + abs(u2))

c_raw = mul_q(f_eff_1,u2) - mul_q(f_eff_2,u1)
c = clamp(c_raw,-Q,Q)

base_g = mul_q(W,CONTEXT_BLEND_Q)
g1 = mul_q(base_g,abs(u1))
g2 = mul_q(base_g,abs(u2))
g3 = mul_q(base_g,abs(c))

target = (u1,u2,c)
S_i' = S_i + mul_q(g_i,target_i-S_i)
```

No S clipping occurs. Since every gain is in `[0,Q/2]`, the rounded update
remains between its prior S coordinate and target coordinate. The S cube is
therefore invariant under the frozen signed round-half-even arithmetic.

After S update:

```text
if (u1,u2) == (0,0):
    F = (0,0,0)
else:
    F = (u1,u2,FAST_HORIZON_NS)
```

R is updated only after W/F/S. Null semantic input leaves R unchanged. Existing
tokens increment their count with saturation and become open. New tokens are
inserted; if full, the closed entry with lexicographically smallest
`(last_seen_active_time_ns, first_seen_active_time_ns, semantic_event_class)`
is evicted. The current open token is never eligible. Recurrence is
register-window-relative: an evicted token restarts at one if it reappears.

One active visual-time coordinate system exists. R timestamps use the sidecar
committed active time coordinate. F duration is relative, not a second epoch.
Later lifecycle/persistence commits must evolve F by the exact elapsed active
time before committing that corresponding sidecar time.

## Frozen fixture results

At 300 active seconds after dA onset:

```text
H0 S = (0,0,0)
H1 S = (500000,0,0)
```

The retained difference is exactly `500000 q`.

For `d0,dA,dB,d0` versus `d0,dB,dA,d0` with one active second between A and B:

```text
O1 S = (500000,500000,+320000)
O2 S = (500000,500000,-320000)
O1 - O2 = (0,0,640000)
```

The order-sensitive witness is specifically `S.orientation_q`. Replacing c
with zero in a test-only reference evaluation makes both histories exactly
`(500000,500000,0)`.

## Claim ceiling

- W has no claimed nonzero dead-zone width; W is zero only at exact synthetic d0.
- Fixed-point rounding can zero extremely small writes; this is not a continuous
  dead-zone theorem.
- S has no elapsed-time decay; the 300-second result is a minimum survival
  result for this frozen trajectory, not an S half-life.
- Relevant later observations can revise S.
- A zero descriptor coordinate gives zero direct gain for its matching S
  coordinate.
- Orientation history is limited by the five-second F interaction window.
- c-clamping has a real saturation region for extreme legal transitions.
- Recurrence is register-window-relative, not lifetime recurrence.
- Synthetic qualification does not prove arbitrary camera behavior.
- Phase 5 must bind its order-sensitive role to `S.orientation_q`.
- Phase-5 quantization must be independently justified and frozen before Phase
  6; it may not be selected merely to manufacture a pass.
- Phase-4 internal margins do not prove projection distinguishability.

## Identity

```text
schema_id: brainvision.vhe.operator.v1
algorithm_id: fixedpoint-context-a-double-star.v1
manifest_core_sha256:
c367de696ba56b417054336a2ace5e8fd6b6b6a5cb3c7e3fa21f2bac4519d8bb
operator_id:
bvheop1_c367de696ba56b417054336a2ace5e8fd6b6b6a5cb3c7e3fa21f2bac4519d8bb
```

The earlier
`b1cf201d2ed1fd9fa76e1cc5dc67b436a142ff09506ca81a9ff48140117bbca6`
identity was superseded pre-freeze and is not authoritative.

The canonical ASCII core bytes use sorted keys, compact separators,
`ensure_ascii`, and `allow_nan=False`. Those bytes are the operator identity
authority. They contain all load-bearing equations, bounds, identities,
fixture hashes, rounding rules, update order, numerical representation, R
rules, and claim-ceiling behavior. They never contain their own `operator_id`.
Object-form manifest views are fresh decoded copies and cannot alter canonical
bytes or the frozen operator identity.
