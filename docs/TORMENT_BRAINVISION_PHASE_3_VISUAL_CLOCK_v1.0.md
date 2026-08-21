# TORMENT Brainvision Phase 3 Visual Clock v1.0

## Status

This document freezes deterministic accounting of Brainvision-owned active
visual time. It does not define VHE dynamics, configuration, persistence,
lifecycle, ingress, projection, or any TORMENT runtime integration.

## Representation and source

Active visual time is an exact non-negative integer number of nanoseconds.

```text
VISUAL_TIME_NS_PER_SECOND = 1_000_000_000
T_PRODUCT_V1_SECONDS      = 300.0
T_PRODUCT_V1_NS           = 300_000_000_000
```

Therefore 300 seconds is represented exactly as 300,000,000,000 nanoseconds.
Elapsed time is never accumulated in floating point. Production uses
`time.monotonic_ns()` through the injected monotonic-source boundary. Tests use
a deterministic manually controlled source returning exact Python integers;
`bool` and non-integers are rejected.

## Active visual-time state

The primitive owns:

```text
committed_active_time_ns: non-negative exact integer
process_local_origin_ns: exact integer or None
```

While the origin is present, current visual time is:

```text
committed_active_time_ns + (monotonic_ns() - process_local_origin_ns)
```

An absent origin means accumulation is frozen and the current read is exactly
the committed value. The origin is process-local and is never persisted.
Process downtime and frozen duration do not contribute to visual time.

Only `committed_active_time_ns` is eligible for later persistence.
`process_local_origin_ns` is runtime-only and is never serialized. The
injected monotonic source is likewise runtime-only and is never serialized.
Those two runtime-only values are deliberately excluded from the clock's
dataclass persistence-shaped representation.

## Primitive semantics

- Active construction or active reload binds a new origin at `now`; its first
  read equals the supplied committed time, so downtime is not reconstructed.
- Frozen construction has no origin and does not sample the source.
- Reads are pure: they neither commit, rebase, freeze, resume, nor persist.
- Resolve-and-rebase commits `now - origin`, then sets the origin to that same
  sampled `now`. Repeating it without source movement adds exactly zero.
- Freeze resolves once, then clears the origin. Frozen reads remain unchanged
  despite source movement.
- Resume binds a new origin without changing committed time; frozen duration is
  ignored.
- Reset while active sets committed time to zero and binds a fresh origin.
  Reset while frozen sets committed time to zero and remains frozen.
- A source reading earlier than an active process-local origin is a hard
  clock-regression error; it is never clamped to zero.

Later lifecycle work may use these primitives for enable, accepted-observation
commit, resume, reset, reload, and successful shutdown. Phase 3 implements none
of those lifecycle operations.

## Claim ceiling

Phase 3 establishes deterministic accounting of Brainvision-owned active visual
time only. It does not establish VHE dynamics, physical camera timing,
frame-rate invariance, realtime catch-up, lifecycle correctness, persistence
correctness, product-horizon retention, or character behavior.
