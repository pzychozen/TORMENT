# TORMENT Brainvision ΨTRS Boundary-Neutral Companion Prerecorded Findings v0.9

## 1. Status / quarantine

**DOCS-ONLY findings synthesis. Non-authorizing, non-implementing.** This note records a bounded,
descriptive engineering reading of an existing, already-generated boundary-neutral companion replay of the
prerecorded ΨTRS paired analysis. It builds nothing and changes nothing. It parses two existing external
JSON replays to verify their arithmetic and to describe what the output already contains.

Work stays quarantined under `research/brainvision/` + `tests/research/`. This note does **not**: change
code; change tests; rerun the analyzer; create new controls or inputs; alter existing JSON outputs; copy
generated JSON into the repository; commit or push; update `§0`; update registry or orientation pointers;
or open any runtime, live-capture, camera, sensor, memory, prompt, context, action, MCP, movement,
autonomy, render-body, database, substrate, carrier, or Stage-B route. It makes no perception, vision,
scene-understanding, object-recognition, learning, temporal-order, arrow-of-time, causality, mechanism,
classifier, inference, or significance claim.

Governing standing (preserved exactly):

```text
FORMAL_HOLD_active                 = True
Mode_0_active                      = True
verdict                            = HOLD

documentation_authorized           = True
existing_output_parsing_authorized = True
new_experiment_authorized          = False
implementation_change_authorized   = False
scientific_claim_authorized        = False
runtime_integration_authorized     = False
```

## 2. Governing sources

Method semantics are authoritatively defined by the committed specifications and implementation; the
external JSON is treated as generated evidence, not repository authority.

```text
docs/TORMENT_BRAINVISION_PSI_TRS_REAL_VIDEO_BOUNDARY_NEUTRAL_DUAL_REPORTING_DESIGN_v0.6.md
docs/TORMENT_BRAINVISION_PSI_TRS_BOUNDARY_NEUTRAL_COMPANION_FORMAL_SPECIFICATION_v0.7.md
docs/TORMENT_BRAINVISION_PSI_TRS_BOUNDARY_NEUTRAL_COMPANION_IMPLEMENTATION_DECISION_v0.8.md
research/brainvision/run_prerecorded_paired_analysis_v0_1.py
  (commit 6b4dd2c "research(brainvision): implement boundary-neutral psi companion")
```

Naming convention used throughout: **"boundary-neutral psi_trs companion metric"** (equivalently
**"all-start psi_trs reference"**) for the O1/A3 aggregate, and **"raw fixed-start psi_trs"** for the
historical single-start response. The companion is **not** called "vision."

## 3. Evidence provenance and deterministic-replay standing

The findings below are read from two external, non-repository JSON artifacts, each generated from the same
nine approved `.npz` inputs with `--with-boundary-neutral-companion --format json`. Both are held outside
the repository and are **not** copied into it.

```text
artifact 1 = boundary_neutral_run1.json
artifact 2 = boundary_neutral_run2.json
size (each)      = 2,127,186 bytes
SHA-256 (each)   = ae2723f272ecc2f513ac910b4d045ca7ab392a5e31856482fcfa58763a487370
stderr (each)    = empty
Windows FC       = no differences encountered
```

Because both replays are byte-identical (equal SHA-256, equal size, empty stderr, `FC` clean),
deterministic replay is confirmed byte-for-byte on this fixture set. The two artifacts are therefore
interchangeable for this reading; all numbers below were recomputed from `boundary_neutral_run1.json` and
apply equally to `boundary_neutral_run2.json`.

**Independent verification.** Every numerical value recorded in this note was recomputed directly from the
JSON per-start responses, per-block records, and denominators — not read back from the file's own summary
fields — and each recomputed value matched the recorded value to its stated precision. No discrepancy was
found. One method note, cross-checked against the data rather than assumed: the raw fixed-start psi_trs
response for a block equals that block's companion per-start response at start `s = 0`
(`raw = companion_response + raw_minus_companion`), consistent with the v0.7 contract.

## 4. Document purpose — distinctions maintained

This record deliberately keeps the following distinct and does not let one stand in for another:

1. the mathematical start-invariance of the all-start aggregate;
2. the observed distribution of responses across the 64 starts;
3. the response to a relatively circular-shifted control;
4. raw fixed-start measurements;
5. boundary-neutral companion measurements;
6. facts present in the output;
7. interpretations that remain unauthorized.

The central and easily-confused point is stated exactly, and **not** as a claim that circular sensitivity
"vanished":

```text
The companion scalar removes dependence on which global circular start is selected because all 64 starts
are included. A relatively circular-shifted control can nevertheless retain a nonzero response. These are
different properties.
```

## 5. Run inventory

```text
analysis type                         = DESCRIPTIVE_PAIRED_ENGINEERING_ANALYSIS
analyzer                              = TORMENT_BRAINVISION_PRERECORDED_PAIRED_ANALYSIS v0.1
global seed                           = 20260716
block length                          = 64
clips                                 = 9
complete blocks per clip              = 4
controls per block                    = 6, including true
companion descriptors                 = psi_trs and psi_trs_k0
starts per descriptor/control/block   = 64
block/control records                 = 216
descriptor-level companion records    = 432
per-start normalized responses        = 27,648
```

Inputs:

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

Blocks are non-overlapping within each clip, but they are **not** claimed to be statistically independent.

## 6. Numerical-health findings

```text
nonfinite per-start responses         = 0
epsilon hits                          = 0
near-epsilon hits                     = 0
minimum raw psi_trs denominator       = 43.61952352118088
minimum raw psi_trs_k0 denominator    = 45.311178335448425
maximum raw psi_trs denominator       = 48.10791596162972
maximum raw psi_trs_k0 denominator    = 51.234265466125834
```

No observed result depended on epsilon flooring or near-zero denominator behavior (zero epsilon hits and
zero near-epsilon hits across all 27,648 per-start evaluations). Every true-control response was exactly
zero for both companion descriptors across all clips, blocks, and starts (the matched true/true difference
is identically zero). This numerical health is a fact about **this exact fixture set only** and is not
generalized beyond it.

## 7. Descriptive aggregate table

Arithmetic means across the 36 block records (9 clips × 4 blocks) for each non-true control:

| Control            | Raw psi_trs | Companion psi_trs | Companion psi_trs_k0 | Companion recursive delta | Raw-to-companion psi_trs change |
| ------------------ | ----------: | ----------------: | -------------------: | ------------------------: | ------------------------------: |
| time_shuffled      |    0.178740 |          0.186694 |             0.182639 |                 +0.004055 |                      +4.449666% |
| descriptor_dropout |    0.158700 |          0.160440 |             0.164933 |                 -0.004493 |                      +1.096619% |
| channel_shuffle    |    0.140823 |          0.147943 |             0.144911 |                 +0.003032 |                      +5.055844% |
| time_reversed      |    0.044747 |          0.045147 |             0.004405 |                 +0.040742 |                      +0.893045% |
| circular_shift     |    0.041910 |          0.034054 |             0.004766 |                 +0.029288 |                     -18.744642% |

Definitions:

```text
companion_recursive_delta = companion_response_psi_trs - companion_response_psi_trs_k0

Raw-to-companion psi_trs change (%) =
  ((mean companion psi_trs - mean raw psi_trs) / mean raw psi_trs) × 100
```

In the change-percentage convention, "mean companion psi_trs" and "mean raw psi_trs" are the unweighted
arithmetic means across the same 36 block records (9 clips × 4 blocks) used in the table above. The existing
percentage values are reported as generated and are not recomputed or altered here.

This table is an unweighted descriptive mean across block records. It is **not** an inferential estimate,
and no weighting, pooling, or cross-block inferential object is constructed from it.

## 8. Per-clip control standing

Using the median companion `psi_trs` response across the four blocks of each clip:

```text
time_shuffled ranked highest in 8 of 9 clips
descriptor_dropout ranked highest in clip6_chaotic
```

This is a descriptive ranking of a matched-transform-sensitivity magnitude. It is **not** classification
accuracy, predictive performance, or a discrimination result.

## 9. Recursive-delta observations

Block-level companion recursive-delta signs (across the 36 blocks per control):

```text
time_reversed:
  positive companion recursive delta = 36 / 36 blocks
circular_shift:
  positive companion recursive delta = 36 / 36 blocks
time_shuffled:
  positive companion recursive delta = 23 / 36 blocks
  negative companion recursive delta = 13 / 36 blocks
descriptor_dropout:
  positive companion recursive delta = 16 / 36 blocks
  negative companion recursive delta = 20 / 36 blocks
channel_shuffle:
  positive companion recursive delta = 16 / 36 blocks
  negative companion recursive delta = 20 / 36 blocks
```

At the clip-median level (median across each clip's four blocks):

```text
time_reversed:
  raw positive       = 9 / 9
  companion positive = 9 / 9
circular_shift:
  raw positive       = 9 / 9
  companion positive = 9 / 9
time_shuffled:
  raw positive       = 3 / 9
  companion positive = 7 / 9
```

For time shuffle, the four clips whose median changed from negative raw delta to positive companion delta:

```text
clip2.npz
clip4.npz
clip5_static.npz
clip8_periodic.npz
```

Also:

```text
clip1.npz and clip9_degraded.npz remained negative
clip3.npz, clip6_chaotic.npz, and clip7_hardcut.npz were already positive
```

The permitted interpretation is only:

```text
The fixed start materially affected the earlier descriptive recursive-delta sign for time shuffle in this
fixture set.
```

The positive reversal and circular results are **not** interpreted as proof of temporal direction,
recurrence correctness, causality, or mechanism validity.

## 10. Start-distribution findings

Scalar start-invariance of the all-start aggregate does **not** imply uniform per-start responses. The
per-start distributions can be broad and asymmetric even when the aggregate scalar is invariant to the
global start.

The following extrema were identified across eligible finite non-true `psi_trs` block/control records in
this nine-clip run. Matched `true` records were excluded from ratio comparisons because their responses and
medians are zero, making the relevant ratios undefined. This domain — finite non-true block/control
records — applies to all three extrema below: the largest relative IQR, the largest maximum-to-median
ratio, and the largest absolute raw-to-companion psi_trs change (the absolute-change search was likewise
conducted over finite non-true block/control records). All three identified extrema fall on
`circular_shift` records.

Three examples (each a single block/control record; all are `circular_shift`):

### Largest relative IQR

```text
clip2.npz
control = circular_shift
block = 0
raw psi_trs             = 0.078457
companion psi_trs mean  = 0.040238
median                  = 0.036400
IQR                     = 0.040465
minimum                 = 0.003191
maximum                 = 0.085296
IQR / mean              = 1.005645
```

### Largest maximum-to-median ratio

```text
clip9_degraded.npz
control = circular_shift
block = 1
raw psi_trs             = 0.053535
companion psi_trs mean  = 0.047454
median                  = 0.031501
IQR                     = 0.038413
minimum                 = 0.004892
maximum                 = 0.155885
maximum / median        = 4.948503
```

### Largest absolute raw-to-companion psi_trs change

```text
clip3.npz
control = circular_shift
block = 0
raw psi_trs             = 0.106853
companion psi_trs       = 0.063084
raw minus companion     = +0.043768
median                  = 0.056200
IQR                     = 0.050058
minimum                 = 0.006422
maximum                 = 0.131100
```

Circular shift dominates the strongest observed start-instability examples (all three extrema fall on
`circular_shift` records). Permitted conclusion:

```text
A single fixed start can materially overstate or understate the reported psi_trs response. Therefore the
companion scalar should remain accompanied by its per-start distribution diagnostics.
```

This does **not** establish a population distribution or a statistical uncertainty interval; the 64 starts
are a deterministic enumeration over one block, not a sample from a population.

## 11. Bounded interpretation — supported engineering findings

1. The earlier fixed-start `psi_trs` output contained material start-position dependence.
2. O1/A3 successfully produces a scalar that is neutral to the selected global circular start by
   construction.
3. A relatively circular-shifted control remains nonzero; boundary neutrality is not shift equivalence.
4. Reversal and circular controls retain positive `psi_trs - psi_trs_k0` companion deltas across all 36
   blocks in this fixture set.
5. Time-shuffle recursive-delta signs changed materially after all-start aggregation.
6. Some per-start distributions remain broad and asymmetric enough that the scalar alone would conceal
   relevant behavior.
7. No denominator or nonfinite failure occurred in the approved nine-clip run.
8. Deterministic replay succeeded byte-for-byte.

## 12. Mandatory non-claims

This run does **not** establish any of:

```text
vision
perception
scene understanding
object recognition
learning
improved intelligence
temporal understanding
temporal-order proof
arrow of time
causality
recursive mechanism validity
biological plausibility
classifier performance
generalization
independent inference
statistical significance
production readiness
runtime suitability
live capture readiness
memory integration
action integration
MCP or movement readiness
```

The report's explicit status is preserved:

```text
scientific_evidence_generated     = False
independent_inference_authorized  = False
perception_claim_authorized       = False
recursive_time_claim_authorized   = False
temporal_order_claim_authorized   = False
```

## 13. Disposition

```text
findings_status =
  BOUNDED_DESCRIPTIVE_ENGINEERING_FINDINGS_RECORDED
boundary_neutral_companion_status =
  IMPLEMENTED_TESTED_AND_REPLAYED_ON_APPROVED_FIXTURES
deterministic_replay_status =
  BYTE_IDENTICAL_PASS
denominator_health_on_current_fixtures =
  PASS_WITHOUT_EPSILON_OR_NEAR_EPSILON_EVENTS
fixed_start_dependence =
  MATERIALLY_PRESENT_IN_SELECTED_BLOCKS
relative_circular_control_response =
  REMAINS_NONZERO
temporal_order_claim =
  NOT_AUTHORIZED
perception_or_vision_claim =
  NOT_AUTHORIZED
new_experiment_status =
  NOT_AUTHORIZED
runtime_integration_status =
  NOT_AUTHORIZED
```

## 14. Future directions (recorded, not authorized, not scheduled)

The following bounded fork is recorded only. No option is chosen here; each requires separate review and
authorization.

```text
A. freeze the current psi_trs companion phase and use it only as a documented offline diagnostic;
B. construct a second independent fixture family to test whether the observed reversal/circular delta
   pattern reproduces;
C. design a stronger order-specific falsifier whose target cannot be reduced to boundary choice or
   spectrum-level properties;
D. close this Brainvision subphase and return to the broader offline learning-over-time benchmark.
```

*End — TORMENT Brainvision ΨTRS Boundary-Neutral Companion Prerecorded Findings v0.9. Docs-only,
non-authorizing, non-implementing. External JSON treated as generated evidence, not repository authority;
committed specifications and implementation remain authoritative for method semantics. No `§0` pointer; no
registry or orientation update; no new implementation decision; no tags.*
