# TORMENT Brainvision Phase 2 Observation Contract v1.0

## Status

This document freezes the Phase-2 typed `FIRSTHAND_VISUAL` observation
contract and its synthetic descriptor-level qualification fixtures. It does
not define visual time, VHE dynamics, projection, lifecycle, persistence,
Fabric integration, ingress, or model integration.

## Low-level descriptor

The descriptor schema identity is `brainvision.low_level_descriptor.v1`. Its
mathematical coordinate order is:

1. `mean_luminance_q`
2. `mean_adjacent_luminance_difference_q`

This coordinate order is independent of canonical JSON textual key order.
Canonical JSON uses `sort_keys=True`; JSON key order MUST NOT be used to infer
descriptor coordinate order.

Both fields are exact Python integers in the inclusive range `0..1_000_000`.
`bool` is not an integer for this contract. The scale is `Q_SCALE = 1_000_000`.
For normalized upstream value `x` in `[0, 1]`, the upstream adapter computes
`q = round-half-even(x * Q_SCALE)`. The Brainvision DTO receives those exact
integers and never receives or coerces floats.

`mean_luminance_q` is the fixed-point arithmetic mean of the
adapter-contract-defined normalized luminance analysis plane.
`mean_adjacent_luminance_difference_q` is the fixed-point arithmetic mean
absolute luminance difference over the adjacency relation defined by that
adapter contract. A spatially uniform analysis plane has adjacent difference
zero.

Each descriptor channel derives from exactly one visual observation. No
channel may become temporal or multiframe under this schema. Brainvision does
not define raw image resolution, resampling, transfer function, photometry,
colour-to-luminance conversion, adjacency, or border handling.

## Observation envelope

The observation schema identity is
`brainvision.firsthand_visual_observation.v1`. The canonical mapping contains
exactly these fields; optional fields are present as `null`, never omitted:

```text
schema_id
provenance_type
stream_identity
source_sequence
observation_id
descriptor
adapter_id
adapter_contract_id
source_capture_time_unix_ns
confidence_q
semantic_event_class
world_event_id
```

`provenance_type` is the closed discriminator `FIRSTHAND_VISUAL`. No
adapter-controlled `admitted` flag exists. Later ingress decides admission;
this DTO validates shape and deterministic identity only.

`stream_identity`, `adapter_id`, and `adapter_contract_id` each use the ASCII
token syntax `^[a-z][a-z0-9._-]{0,63}$`. `source_sequence` is an exact integer
in `0..9223372036854775807`; Phase 2 does not enforce replay progression.
`source_capture_time_unix_ns`, when present, is an exact signed 64-bit integer.
`confidence_q`, when present, is an exact integer in `0..1_000_000` and is
admission/provenance metadata only.

`semantic_event_class`, when present, is the opaque namespaced token
`^[a-z][a-z0-9_-]{0,31}:[a-z][a-z0-9._-]{0,63}$`. It is not free text and does
not create a semantic taxonomy. `world_event_id`, when present, uses
`^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$`.

`adapter_contract_id` identifies the parameterized measurement contract, not
merely adapter software. A changed analysis resolution, resampling kernel,
transfer function or photometry, colour-to-luminance conversion, adjacency,
border handling, or any other descriptor-semantic parameter requires a new
identifier. Phase 8 binds one such identifier to the configured stream
lineage; Phase 11 refuses a mismatch. Neither it nor `confidence_q` may affect
F/S/W numerical dynamics. `source_sequence`, `observation_id`, capture time,
and `world_event_id` remain dynamically inert as required by Phase 0.

Adapter-supplied visual time, lifecycle, configuration, watermark, VHE, and
projection fields are forbidden. The strict field set rejects them rather than
silently ignoring them.

## Observation identity

The identity schema is `brainvision.observation-id.v1`. It binds exactly
`(stream_identity, source_sequence)` and no descriptor, semantic, adapter,
confidence, timestamp, or world-event field.

The canonical identity payload uses ASCII JSON with `sort_keys=True`,
`separators=(",", ":")`, `ensure_ascii=True`, and `allow_nan=False`. For
`stream_identity = "cam-a"` and `source_sequence = 7`, it is:

```json
{"identity_schema":"brainvision.observation-id.v1","source_sequence":7,"stream_identity":"cam-a"}
```

The ASCII bytes are URL-safe-base64 encoded, trailing `=` padding is removed,
and `bvobs1_` is prefixed. The required vector is:

```text
bvobs1_eyJpZGVudGl0eV9zY2hlbWEiOiJicmFpbnZpc2lvbi5vYnNlcnZhdGlvbi1pZC52MSIsInNvdXJjZV9zZXF1ZW5jZSI6Nywic3RyZWFtX2lkZW50aXR5IjoiY2FtLWEifQ
```

The supplied `observation_id` must equal this derived value exactly.

## Canonical serialization

Every contract mapping has an explicit schema ID and an exact field set.
Canonical JSON uses `sort_keys=True`, compact separators, ASCII encoding, and
`allow_nan=False`. Missing fields, unknown fields, non-canonical identifiers,
schema mismatches, non-`FIRSTHAND_VISUAL` provenance, floats where integers
are required, and bool-as-int are rejected without coercion.

## Frozen synthetic fixtures

The descriptor-only fixtures contain no semantic event class and are not
asserted to be exact outputs of a noisy physical camera.

| Fixture | `mean_luminance_q` | `mean_adjacent_luminance_difference_q` | SHA-256 |
| --- | ---: | ---: | --- |
| `d0` | 500000 | 0 | `c08e4b0cf384c20b126ea4466ab2122811f5ad2328e2c482bcfea5471d526544` |
| `dA` | 750000 | 0 | `9fdd9ce03853911b050565684b0432079cc4cf3f7e51a4dc035b7423762e7583` |
| `dB` | 500000 | 250000 | `2caa7c6d89da394da758f26ada91658cabb1969639fffd7767130d789c152517` |

Relative to `d0`, `dA - d0 = (+250000, 0)` and
`dB - d0 = (0, +250000)`. These are equal-magnitude orthogonal descriptor-space
displacements. A purely isotropic/permutation-invariant magnitude response to
displacement from `d0` cannot distinguish them. This does not require a
multidimensional internal VHE state.

## Claim ceiling and anti-tuning boundary

- Fixtures cannot change after Phase-4 operator work begins.
- Descriptor channel count, order, meaning, and quantization are part of this
  schema identity.
- No numerical equivalence is claimed across adapter contracts.
- Qualification on these synthetic fixtures does not establish equivalent
  behaviour for arbitrary camera-derived contracts.
- Descriptor resolution does not define projection quantum.
- Acceptance does not establish sign symmetry, physical vision accuracy,
  arbitrary spatial understanding, independent multidimensional VHE state, or
  arbitrary frame-rate invariance.
