# TORMENT Brainvision Prerecorded Operational Harness — First Findings v0.1

## 1. Status / quarantine

**DOCS-ONLY findings synthesis. Non-authorizing, non-implementing.** This note records a bounded, descriptive
engineering reading of an existing, already-generated first operational run of the committed prerecorded
operational harness over nine prerecorded `.npz` clips. It builds nothing and changes nothing. It records the
run's identity, its same-environment replay standing, and what the canonical output already contains; it
selects no threshold, comparability policy, or success criterion, and it makes no scientific claim.

Work stays quarantined under `research/brainvision/` + `tests/research/`. This note does **not**: change code;
change tests; change any existing document; change `psi_trs.py`; change the paired analyzer; change the N64
falsifier; change any production TORMENT file; rerun the harness; copy the canonical output into the
repository; commit or push; update `§0`; update registry or orientation pointers; or open any runtime,
live-capture, camera, sensor, memory, prompt, context, action, MCP, movement, autonomy, render-body,
database, substrate, carrier, or Stage-B route. It makes no perception, vision, temporal-order, arrow-of-time,
causality, classification, statistical-significance, or recursive-mechanism claim.

Governing standing (preserved exactly):

```text
FORMAL_HOLD_active                        = True
Mode_0_active                             = True
verdict                                   = HOLD

documentation_authorized                  = True
existing_output_recording_authorized      = True
new_experiment_authorized                 = False
implementation_change_authorized          = False
scientific_claim_authorized               = False
temporal_order_claim_authorized           = False
perception_or_vision_claim_authorized     = False
runtime_integration_authorized            = False
production_kernel_modification_authorized  = False
```

## 2. Governing sources

Method and orchestration semantics are authoritatively defined by the committed specification, harness, and
paired analyzer; the canonical output is treated as generated evidence, not repository authority.

```text
docs/TORMENT_BRAINVISION_PRERECORDED_OPERATIONAL_HARNESS_IMPLEMENTATION_SPECIFICATION_v0.1.md
research/brainvision/run_prerecorded_operational_harness_v0_1.py
research/brainvision/run_prerecorded_paired_analysis_v0_1.py
```

Descriptor computation is performed solely by the paired analyzer's `analyze_paths(..., include_sag=True,
with_companion=True)`; the harness embeds that result verbatim and adds only the operational envelope. The
recursive-delta and companion standings quoted below are the analyzer's existing, unmodified definitions.

## 3. Frozen operational run identity and same-environment replay

```text
source_commit =
  d007f9500aeff7b1f7a8b6a9d00560895e21626f

canonical_output_sha256 =
  ce557811b9b4bac6d1a0630222ec3b0b7313502eba00948af4f8af0843f314bf

embedded_payload_sha256 =
  c4785c303edc1043e29983b739b11e4cdc2ba1cc95a446e53dcef16017cf3fbc

input_manifest_sha256 =
  a2e77936cd9decf60b757ab8f4e5c743376d8ca9953022423bb17af42adc5e09
```

Two complete runs were performed using the **same ordered nine positional `.npz` path strings**. Their
canonical JSON outputs were byte-identical, their human summaries were byte-identical, and both JSON files
carried the same SHA-256 shown above. Exact same-environment byte replay is therefore established for this
run.

The two runs were approximately twenty minutes apart. **No scientific meaning is inferred from the elapsed
time**; it is recorded only to note that the two executions were separate, and only that exact
same-environment replay held.

## 4. Ordered input set and block structure

Ordered nine-clip positional input (order authoritative; it sets clip ordinals and seed derivation):

```text
clip1.npz
clip2.npz
clip3.npz
clip4.npz
clip5_static.npz
clip6_chaotic.npz
clip7_hardcut.npz
clip8_periodic.npz
clip9_degraded.npz
```

Each clip had the same block structure:

```text
descriptor rows        = 300
complete blocks        = 4
block length           = 64
discarded trailing rows = 44
```

Blocks are non-overlapping within each clip; they are **not** claimed to be statistically independent.

## 5. Harness health

The canonical `harness_health` object reports a fully successful engineering-validity state:

```text
manifest_valid           = True
inputs_readable_valid     = True
analyzer_identity_valid   = True
analysis_completed_valid  = True
clip_count_valid          = True
serialization_valid       = True
replay_material_valid     = True
overall_health            = True
error_codes               = []
```

`overall_health` is the logical AND of the seven booleans above it; it is an engineering-validity fact about
this exact run only and is not a scientific result. Numerical health across the run:

```text
finite descriptor responses     = 1728
nonfinite descriptor responses  = 0
epsilon hits                    = 0
near-epsilon hits               = 0
minimum true-feature norm       ≈ 0.9332679262951696
minimum-norm descriptor         = rpsr
```

The 1728 finite responses correspond to 9 clips × 4 blocks × 8 descriptors × 6 controls; no response depended
on epsilon flooring or a near-zero denominator.

## 6. Reproduced descriptor-control standings

Highest-median control per descriptor, across the nine clips (descriptive matched-transform-sensitivity
ranking):

```text
descriptor_only:
  channel_shuffle highest median in 9/9 clips

frame_diff:
  time_shuffled highest median in 9/9 clips

plain_fft:
  time_shuffled highest median in 9/9 clips

rpsr:
  time_shuffled highest median in 9/9 clips

psi:
  time_shuffled highest in 6/9
  circular_shift highest in 3/9

psi_trs:
  time_shuffled highest in 8/9
  descriptor_dropout highest in 1/9

psi_trs_k0:
  time_shuffled highest in 6/9
  descriptor_dropout highest in 2/9
  channel_shuffle highest in 1/9

random_mapping:
  time_reversed highest in 4/9
  circular_shift highest in 3/9
  time_shuffled highest in 2/9
```

Bounded interpretation: time shuffle is a strong general disruption across multiple descriptors; this is
**not** uniquely ΨTRS-specific. These rankings are descriptive matched-sensitivity magnitudes and are **not**
pass/fail, classification, perception, or temporal-order verdicts.

## 7. Fixed-start recursive-delta standing

Clip-level median recursive-delta signs (across the nine clips):

```text
time_reversed:
  positive = 9/9

circular_shift:
  positive = 9/9

time_shuffled:
  positive = 3/9
  negative = 6/9

channel_shuffle:
  positive = 4/9
  negative = 5/9

descriptor_dropout:
  positive = 2/9
  negative = 7/9
```

Exact standing (analyzer's own definition, preserved verbatim):

```text
positive recursive_delta means greater normalized transform sensitivity of psi_trs than psi_trs_k0.
negative recursive_delta means lower  normalized transform sensitivity of psi_trs than psi_trs_k0.
```

It does **not** mean better perception, better temporal-order detection, scientific superiority, or a
validated recursive-time mechanism.

## 8. Boundary-neutral companion standing

The companion used the boundary-neutral policy:

```text
offset policy = O1 — all 64 starts
aggregation   = A3 — mean normalized response across matched starts
```

Clip-level companion median signs:

```text
time_reversed:
  positive = 9/9

circular_shift:
  positive = 9/9

time_shuffled:
  positive = 7/9
  negative = 2/9

channel_shuffle:
  positive = 5/9
  negative = 4/9

descriptor_dropout:
  positive = 2/9
  negative = 7/9
```

The five clip/control cases whose median sign changed between fixed-start and boundary-neutral companion
reporting:

```text
clip2 / time_shuffled          : negative -> positive
clip4 / time_shuffled          : negative -> positive
clip5_static / time_shuffled   : negative -> positive
clip8_periodic / time_shuffled : negative -> positive
clip8_periodic / channel_shuffle : negative -> positive
```

Across individual block/control comparisons:

```text
fixed-start versus all-start sign differences = 15 of 216
```

Interpretation: start position materially affects some cases; the all-64-start companion is therefore
justified as first-class reporting alongside the fixed-start values. Neither fixed-start nor companion output
is a scientific mechanism verdict.

## 9. Block-instability examples

Recorded to displayed precision (each a single clip/descriptor/control record):

```text
clip3 / frame_diff / circular_shift:
  per-block ≈ [0.0054, 5.9590, 0.0040, 0.0029]
  median   ≈ 0.00470

clip7_hardcut / frame_diff / circular_shift:
  maximum  ≈ 1.2843
  median   ≈ 0.01049

clip8_periodic / frame_diff / time_shuffled:
  per-block ≈ [2.1890, 1.4063, 6.0161, 0.8868]
  median   ≈ 1.7976
```

Some clip-level means can be dominated by a single block. Blocks are non-overlapping within a clip but are
**not** asserted to be statistically independent, so a clip mean is not an inferential estimate.

## 10. SAG standing

Strongest mean/median divergence examples:

```text
clip9_degraded / circular_shift : mean_median_ratio ≈ 19.77
clip4 / channel_shuffle         : mean_median_ratio ≈ 17.33
clip5_static / true             : mean_median_ratio ≈ 8.65
```

SAG top-control counts across the nine clips:

```text
time_shuffled   = 5 clips
circular_shift  = 3 clips
channel_shuffle = 1 clip
```

The `true` sequence ranked from third to sixth and **never ranked first**.

Interpretation: SAG amplification must **not** be treated as an ordered-video, perception, or temporal-order
score; means and medians can differ drastically due to block-level concentration.

## 11. Strongest all-start skew example

```text
clip9_degraded / circular_shift / block 1 / psi_trs_k0:
  mean             ≈ 0.002050
  median           ≈ 0.000137
  mean_median_ratio ≈ 14.96
  maximum          ≈ 0.014924
```

This is interpreted only as a rare-start spike pattern (a few starts elevated) rather than a uniformly
elevated response; it is not a mechanism, perception, or temporal-order signal.

## 12. Disposition

```text
OPERATIONAL_HARNESS_FIRST_RUN            = PASS
EXACT_REPLAY                             = PASS
INPUT_AND_ENVIRONMENT_IDENTITY_CAPTURED  = True
FINITE_NUMERICS                          = PASS

EARLIER_PAIRED_FINDINGS_REPRODUCED         = True
BOUNDARY_NEUTRAL_REPORTING_JUSTIFIED       = True
START_POSITION_MATERIALLY_AFFECTS_SOME_CASES = True
BLOCK_INSTABILITY_REMAINS_MATERIAL         = True

TEMPORAL_ORDER_PROOF            = False
PERCEPTION_OR_VISION_EVIDENCE   = False
RECURSIVE_MECHANISM_VALIDATED   = False
SCIENTIFIC_INFERENCE_AUTHORIZED = False

result_status =
  VALID_REPRODUCIBLE_DESCRIPTIVE_OPERATIONAL_RESULT
```

PASS here means engineering pass — a valid, reproducible, descriptive operational result — not scientific
validation. The reproduced paired and companion standings are descriptive; determinism is an engineering
property only.

## 13. Next direction (recorded, not authorized beyond this record)

```text
1. preserve the canonical output and this findings record as frozen evidence;
2. continue using the operational harness for future prerecorded runs;
3. retain fixed-start and boundary-neutral companion reporting together;
4. continue the independent descriptor-blind witness lane separately;
5. do not modify psi_trs.py, production kernel surfaces, or runtime integration;
6. do not promote scientific, perception, temporal-order, mechanism, or production claims.
```

FORMAL_HOLD and Mode 0 remain active.

*End — TORMENT Brainvision Prerecorded Operational Harness First Findings v0.1. Docs-only, non-authorizing,
non-implementing. Canonical output treated as generated evidence, not repository authority; the committed
specification, harness, and paired analyzer remain authoritative for method semantics. `psi_trs.py`, the
paired analyzer, the N64 falsifier, and the production TORMENT memory kernel are unmodified. No `§0` pointer;
no registry or orientation update; no tags.*
