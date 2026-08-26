# Trajectory V2 Qualification Result

## Scope

Trajectory V2 changes diagnostic persistence and observability only. It does
not change kernel mathematics, SeedWorld physics, memory scoring, retrieval,
deduplication, compression, Character, Hivemind, Brainvision, or cognition.

The initial production freeze retains the legacy trajectory format as the
default. V2 remains explicitly selectable with
`TORMENT_TRAJECTORY_FORMAT=v2`; legacy remains explicitly selectable with
`TORMENT_TRAJECTORY_FORMAT=legacy`.

## Superseded developmental evidence

The first live V2 N=100 qualification is retained as superseded developmental
evidence; it is not deleted or rewritten. It recorded 102 public ingest calls,
102 trajectory frames, 100 native logical steps, 5,868 readable V2 dynamic
records, and 358,731 V2 trajectory bytes. It formally failed because its
experimental format treated repeated native logical steps (25 and 90) as an
invalid `(step, eid)` collision, and did not distinguish an active current
partial from an orphaned crash partial.

The repaired V2 schema introduces the observational frame identity
`(epoch, frame_seq)` and dynamic-record identity `(epoch, frame_seq, eid)`.
Repeated logical steps across distinct frame sequences are native-valid.
The repaired schema does not interpret the superseded experimental artifact as
the current format.

## Qualified results

| Qualification | Legacy trajectory | V2 trajectory | Reduction |
| --- | ---: | ---: | ---: |
| N=100 | 2,018,557 B | 360,227 B | 82.15% |
| N=500 | 46,949,423 B | 7,406,299 B | 84.224941% |

For N=500, the legacy workspace measured 66,262,279 B and the sealed V2
workspace measured 22,615,608 B: a 65.869559% workspace reduction.

Both formats retained 129,648 dynamic observations over 502 frames and 500
logical steps. Logical steps 125 and 450 each occur in two distinct,
native-valid trajectory frames.

All V2 qualification targets passed:

- sealed verification;
- full V1 completeness;
- bit-exact Float64 round trip;
- frame-sequence continuity and population checks;
- EID digest, chunk hashes, and manifest hash chain.

Retrieval and cognitive results were exactly equivalent in the N=500
comparison: sentinel recall@8 1.0, MRR 0.8055555555555557, median rank 1,
contradiction recall 1.0, and noise interference 0.0. Target ranks,
distinct source-backed EIDs (479), derived native EIDs (26), half-life and
strength distributions, and duplicate reinforcement records also matched
exactly. Observer purity was true.

On a copy of the sealed N=500 workspace, SQLite rebuilt 129,648 trajectory
records, retained repeated logical steps by `(epoch, frame_seq, eid)`, and
passed legacy, entity, and all endpoint modes plus the selected-EID visualizer
path.

## Promotion basis

V2 is qualified as a lossless trajectory persistence format. Its promotion
changes only the default selection; the legacy reader and writer remain
supported for explicit compatibility use.
