# TORMENT Memory Substrate — 7G5D1O half-life storage-input identity

## Result

This is a bounded, read-only characterization followed by the separate
`D1_IDENTIFIED_DEFECT_REGRESSION_V2` profile. It did not create a formal
administration, alter the original D1 result, select a production runtime, or
change a half-life formula.

```text
D1_ORIGINAL_RESULT = VALID / STORAGE_SUBSTRATE_DEFECT / 53 historical differences
REGRESSION_V1_DIFFERENCE_COUNT = 4 (half_life_days only; retained unchanged)
REGRESSION_V2_RUN = PASS
REGRESSION_V2_DIFFERENCE_COUNT = 0

D1-STORAGE-03B = UPSTREAM_RECOMPUTATION / REGRESSION_INPUT_IDENTITY_MISMATCH
NATIVE_STORAGE_DEFECT = NO
NATIVE_HALF_LIFE_REPAIR_REQUIRED = NO
FILES_CHANGED_FOR_NATIVE_REPAIR = NONE
```

V2 changes only the four named 03B `half_life_days` comparisons. It compares
the sealed half-life fact that native received with native durable storage;
the independently replayed legacy HTTP result remains an upstream
characterization. All other V1 durable-state comparators remain unchanged.

## A/B/C/D evidence

The V1 artifact pre-check proved that each frozen value A exactly matched the
previously recorded qualified-native value B. The fresh qualified V2 run then
independently reproduced B and recorded the fresh legacy values C and D.
All comparisons use the frozen D1 scalar tolerance (`absolute tolerance
1e-6`); every A/B comparison had zero differences.

| Fixture | A: sealed half-life fact | B: native durable | C: fresh legacy durable | D: fresh legacy HTTP signal | A = B |
| --- | ---: | ---: | ---: | ---: | --- |
| `CORE-M3-distinct` | 99.33128211275871 | 99.33128211275871 | 99.03724640692022 | 99.33128211275871 | YES |
| `CORE-M4-contradiction` | 99.55574927563462 | 99.55574927563462 | 99.26763448262744 | 99.55574927563462 | YES |
| `CORE-S-distinct` | 93.3092862907214 | 93.3092862907214 | 92.39835612104098 | 93.3092862907214 | YES |
| `CORE-S-contradiction` | 93.19844095045838 | 93.19844095045838 | 91.96584731485419 | 93.19844095045838 | YES |

For every row, A differs from C and C differs from D. Crucially, D equals A:
the legacy kernel did not produce a different base signal in this replay.
The divergence occurred in the legacy Fabric pre-write transform between that
signal and the value supplied to `MemoryGraph.spawn_memory()`.

## Write laws and same-input result

The normal legacy path calculates:

```text
kernel signal half-life = 20 + 80 * coherence
Fabric half_life_days = max(1, signal * identity.decay_scale * hl_mult)
hl_mult = clip((1 + 0.20 * tanh(survival_steps / 200))
               * (1 - 0.15 * tearing_risk), 0.85, 1.25)
Fabric -> MemoryGraph.spawn_memory(half_life_days)
payload["half_life"] = float(half_life_days)
```

`MemoryGraph` therefore does not clamp, round, decay, or otherwise transform
its supplied input before durable publication. The qualified native path is
equally direct:

```text
NativeFabricRouteRequest.half_life_days
-> NativeMemoryMotifCompositionRequest.half_life_days
-> payload["half_life"] = float(request.half_life_days)
-> compatibility read view
```

The disposable same-input experiment bypassed HTTP cognition and embeddings.
For each input, both the actual legacy `MemoryGraph.add_memory()` primitive and
the qualified native CREATE route stored exactly the supplied float:

| Input | Legacy durable | Native durable |
| ---: | ---: | ---: |
| 0.5 | 0.5 | 0.5 |
| 0.95 | 0.95 | 0.95 |
| 99.33128211275871 | 99.33128211275871 | 99.33128211275871 |
| 99.55574927563462 | 99.55574927563462 | 99.55574927563462 |
| 93.3092862907214 | 93.3092862907214 | 93.3092862907214 |
| 93.19844095045838 | 93.19844095045838 | 93.19844095045838 |

```text
LEGACY_STORAGE_WRITE_TRANSFORMS_HALF_LIFE = NO
NATIVE_STORAGE_WRITE_TRANSFORMS_HALF_LIFE = NO
SAME_INPUT_LEGACY_NATIVE_PARITY = YES
```

## Fresh legacy pre-write characterization

The effective legacy pre-write multiplier, its actual dynamic inputs, and the
inferred identity factor were captured from the normal HTTP response and its
selected durable payload. `survival_steps` was zero in every row, and the
inferred `identity.decay_scale` was one (within floating-point noise).

| Fixture | tearing risk | `hl_mult` / effective multiplier | inferred `decay_scale` |
| --- | ---: | ---: | ---: |
| `CORE-M3-distinct` | 0.019734347500902222 | 0.9970398478748647 | 1.0 |
| `CORE-M4-contradiction` | 0.01929336377547209 | 0.9971059954336792 | 1.0 |
| `CORE-S-distinct` | 0.06508320917757723 | 0.9902375186233634 | 0.9999999999999999 |
| `CORE-S-contradiction` | 0.08816983224425418 | 0.9867745251633618 | 1.0000000000000002 |

Thus the observed C values are D multiplied by the live `tearing_risk`
component of Fabric's normal pre-write calculation. The sealed native request
was built from the captured response signal (`signals.half_life`), whereas the
legacy payload was written from Fabric's post-multiplier `half_life_days`.
That is the precise input-identity mismatch; it is neither a SQLite
persistence difference nor a native formula defect.

The sealed `half_life_days` carrier is a frozen cross-runtime storage-facing
fact, but it is not the direct argument passed to legacy
`MemoryGraph.spawn_memory()` during a fresh HTTP replay. That direct legacy
argument is C, after Fabric has recomputed the permitted pre-write multiplier.
V2 treats C as `UPSTREAM_RECOMPUTATION_CHARACTERIZATION`, not as the
storage-layer comparator for the four named 03B facts.

The immutable L0 does contain a `created_ts` (`1788172879`) and legacy
retrieval decay reads aging timestamps. Source inspection establishes that
`TriOctaMemoryKernel.process()` runs before `graph.search_by_embedding()` in
ingest, and the kernel signal producer does not read the wall clock. No clock
was frozen.

```text
LEGACY_HTTP_REPLAY_TIME_INVARIANT = YES
HALF_LIFE_UPSTREAM_PRODUCER = TriOctaMemoryKernel.process + TormentFabric pre-write multiplier
HALF_LIFE_DIFFERENCE_CAUSE = fresh Fabric tearing-risk multiplier applied before legacy durable write
```

## Qualification and retained boundaries

The focused half-life and D1-identified-defect tests passed under
`torment-substrate` (Python 3.11.15, sqlite3 module 2.6.0, SQLite 3.53.4).
The actual V2 replay also preserved zero post-write differences, M5 no-write
absence, all structural witnesses, and both independent native contradiction
creates.

```text
D1_ORIGINAL_RESULT_UNCHANGED = YES
POST_WRITE_PASS_PRESERVED = YES
M5_PASS_PRESERVED = YES
STRUCTURAL_PASS_PRESERVED = YES
NEW_FORMAL_ADMINISTRATION = NO

7G5D1O_03B_RESOLVED = YES
D1_IDENTIFIED_STORAGE_DEFECTS_REMAINING = 0

NATIVE_ACTIVE = NO
DUAL_WRITE = NO
DUAL_READ = NO
CUTOVER_OPENED = NO
```
