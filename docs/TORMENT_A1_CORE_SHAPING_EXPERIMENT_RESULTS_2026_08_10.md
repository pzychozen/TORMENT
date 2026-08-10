# TORMENT A1 Core-Shaping Stage-1 Results - 2026-08-10

## Scope

This document preserves the completed Stage-1 paired replay result for `TORMENT_COGNITION_CORE_SHAPING_V1`.

It records only read-only scientific analysis of the completed artifacts under:

```text
C:\TORMENT\TORMENT_stage1
```

No TORMENT behavior, production code, tests, replay outputs, basins, or the frozen experiment design are changed by this record.

## Experiment Identity

Frozen design commit:

```text
495f4c634ef4b21f8ba7035fc2abb1ffd17de613
```

Frozen corpus:

```text
SHA-256: 91309aa25b19189ce0a96e8a6ecb36167dbf92b08c1f50820b539d084a58a6a8
total: 259 distinct historical user queries
PRIMARY: 28
EXTENDED: 231
```

Replay arms:

| Arm | Start UTC | End UTC | Completed |
|---|---:|---:|---:|
| control | `2026-08-10T03:04:45.106532Z` | `2026-08-10T03:05:09.090646Z` | 259 / 259 |
| treatment | `2026-08-10T03:12:46.948714Z` | `2026-08-10T03:13:10.384675Z` | 259 / 259 |

Control-end to treatment-start separation:

```text
7.6309678 minutes
```

## Integrity

Input and runtime integrity relevant to response comparison:

- Frozen source remained unchanged: `SOURCE_PRE` and `SOURCE_POST` both contain 21 files, with exact relative-path, byte-count and SHA-256 identity.
- Both disposable copies began equivalent to the frozen source: `CONTROL_COPY_PRE == SOURCE_PRE` and `TREATMENT_COPY_PRE == SOURCE_PRE` for all 21 files.
- Control flag proof: `TORMENT_COGNITION_CORE_SHAPING_V1.effective_value = false`, `read_timing = import_time`.
- Treatment flag proof: `TORMENT_COGNITION_CORE_SHAPING_V1.effective_value = true`, `read_timing = import_time`.
- Both arms used the same non-degraded embedder: `st`, `BAAI/bge-small-en-v1.5`, CPU, dimension 384.
- Both arms completed 259 / 259 `/agent/query` calls.
- Replay metadata allowed only `GET /health`, `GET /config`, `GET /debug/metrics`, and `POST /agent/query`.
- No `/agent/ingest`, provider call, or `/agent/trace` call was part of the replay.
- Category-A retrieval content remained unchanged.
- Runtime differences were SQLite state only.
- Control and treatment post-shutdown/post-replay manifests both show `workspaces/lived_use_eira_voss_a0/agents/eira_voss/index/memory_index.sqlite` changed. The control arm also showed transient `memory_index.sqlite-shm` and `memory_index.sqlite-wal` files at post-replay before the post-shutdown manifest.

## Qualification

Offline qualification recomputation produced the preregistered totals:

```text
PRIMARY qualifying = 1
EXTENDED qualifying = 9
TOTAL qualifying = 10
NONQUALIFYING = 249
```

## Structural Result

All 249 nonqualifying pairs were structurally identical. No nonqualifying query showed a retrieval-structure difference attributable to the shaping flag.

Qualifying relationship counts:

```text
EXACT_PLUS_ONE = 6
MEMBERSHIP_CHANGED_MORE_COMPLEXLY = 4
NO_PROVIDER_VISIBLE_DIFFERENCE = 0
UNEXPECTED = 0
```

## q0238 PRIMARY Result

`q0238` is the sole preregistered qualifying PRIMARY query.

```text
historical step = 7
control _core_hits_in_count = 6
treatment _core_hits_in_count = 7
treatment-only EID = 19
treatment-only type = episode
treatment rank = 7
identity-bearing = no
classification = EXACT_PLUS_ONE
```

`q0238` did not increment any frozen Stage-2 counter:

```text
PRIMARY_TREATMENT_ONLY_RANK_1_TO_3 = no
ALL_TREATMENT_ONLY_RANK_1_TO_3 = no
ALL_IDENTITY_BEARING_TREATMENT_ONLY_RANK_1_TO_5 = no
```

## Strongest Observed Treatment Effect

The strongest treatment effect occurred on `q0031`:

```text
subset = EXTENDED
historical step = 23
treatment-only EID = 6
type = identity_anchor
treatment rank = 1
```

This increments:

```text
ALL_TREATMENT_ONLY_RANK_1_TO_3
ALL_IDENTITY_BEARING_TREATMENT_ONLY_RANK_1_TO_5
```

It does not increment the PRIMARY counter because it is EXTENDED, not PRIMARY.

## Compact Qualifying Table

| Query | Subset | Historical step | Classification | Treatment-only EID | Treatment rank | Type | Identity-bearing |
|---|---|---:|---|---:|---:|---|---|
| q0004 | EXTENDED | 2 | EXACT_PLUS_ONE | 16 | 7 | episode | no |
| q0007 | EXTENDED | 5 | MEMBERSHIP_CHANGED_MORE_COMPLEXLY | 9 | 4 | episode | no |
| q0031 | EXTENDED | 23 | MEMBERSHIP_CHANGED_MORE_COMPLEXLY | 6 | 1 | identity_anchor | yes |
| q0059 | EXTENDED | 29 | EXACT_PLUS_ONE | 12 | 7 | episode | no |
| q0119 | EXTENDED | 28 | MEMBERSHIP_CHANGED_MORE_COMPLEXLY | 13 | 6 | episode | no |
| q0120 | EXTENDED | 29 | EXACT_PLUS_ONE | 10 | 7 | episode | no |
| q0143 | EXTENDED | 32 | EXACT_PLUS_ONE | 15 | 7 | episode | no |
| q0174 | EXTENDED | 46 | EXACT_PLUS_ONE | 24 | 7 | episode | no |
| q0231 | EXTENDED | 28 | MEMBERSHIP_CHANGED_MORE_COMPLEXLY | 14 | 6 | episode | no |
| q0238 | PRIMARY | 7 | EXACT_PLUS_ONE | 19 | 7 | episode | no |

## Frozen Counters

The frozen Stage-2 counters are:

```text
PRIMARY_TREATMENT_ONLY_RANK_1_TO_3 = 0
ALL_TREATMENT_ONLY_RANK_1_TO_3 = 1
ALL_IDENTITY_BEARING_TREATMENT_ONLY_RANK_1_TO_5 = 1
```

## Numeric Integrity Issue

The preregistered Rev-3 numeric tolerances were:

```text
SIM_ABS_TOLERANCE = 1e-5
FINAL_SCORE_ABS_TOLERANCE = 5e-3
BONUS_COMPONENT_ABS_TOLERANCE = 1e-4
```

Observed numeric result:

```text
max sim delta = 4.186134411965359e-05
sim violations = 1517
max final-score delta = 0.0002543402249688409
final-score violations = 0
max bonus-component delta = 0.0
bonus-component violations = 0
max recency delta error days = 1.090085648157782e-05
recency violations = 0
NUMERIC_TIE_FLIP = []
```

Therefore:

```text
INTEGRITY_PASS = false
```

This is recorded without retroactively changing the frozen tolerance. The result should be treated as a future cross-process numerical-repeatability calibration issue: structurally stable nonqualifying pairs exceeded the strict preregistered `sim` tolerance, while final-score, bonus-component, recency and tie-flip checks remained clean.

## Frozen Stage-2 Result

The frozen gate was:

```text
STAGE2_GATE =
INTEGRITY_PASS
AND (
    PRIMARY_TREATMENT_ONLY_RANK_1_TO_3 >= 1
    OR (
        ALL_TREATMENT_ONLY_RANK_1_TO_3 >= 2
        AND ALL_IDENTITY_BEARING_TREATMENT_ONLY_RANK_1_TO_5 >= 1
    )
)
```

Formal gate evaluation:

```text
INTEGRITY_PASS = false
PRIMARY_TREATMENT_ONLY_RANK_1_TO_3 = 0
ALL_TREATMENT_ONLY_RANK_1_TO_3 = 1
ALL_IDENTITY_BEARING_TREATMENT_ONLY_RANK_1_TO_5 = 1
STAGE2_GATE = false
```

The Stage-2 gate is false in two independent ways:

1. Formally, `INTEGRITY_PASS = false`, so the leading conjunction fails.
2. Independently, the efficacy counters fail the frozen logical threshold: the PRIMARY rank-1-to-3 count is 0, and the ALL rank-1-to-3 count is 1 rather than at least 2.

Frozen result:

```text
CORE_SHAPING_ACTIVATION_TOO_RARE_OR_TOO_WEAK_FOR_NATURAL_LIVED_USE
```

## Scientific Interpretation

Bounded interpretation:

- Core shaping is mechanically active and selective.
- It changed retrieval membership/order structure only on qualifying queries in this corpus.
- Six qualifying cases were exact plus-one cases.
- Four qualifying cases were more complex, consistent with the preregistered treatment relationship model.
- It can occasionally expose a highly promoted memory: one treatment-only `identity_anchor` reached treatment rank 1.
- The observed natural-query activation/effect distribution was insufficient to justify Stage 2 under the frozen gate.
- No behavioral/provider benefit claim is supported by Stage 1.
- No TORMENT tuning is authorized or indicated by this experiment alone.

## Closeout

Stage 1 is preserved as a mechanically informative negative escalation result:

```text
CORE_SHAPING_ACTIVATION_TOO_RARE_OR_TOO_WEAK_FOR_NATURAL_LIVED_USE
```
