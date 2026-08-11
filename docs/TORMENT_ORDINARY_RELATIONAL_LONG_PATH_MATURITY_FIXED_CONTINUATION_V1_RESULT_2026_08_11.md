# TORMENT Ordinary Relational Long Path Maturity Fixed Continuation V1 Result

Preservation date: 2026-08-11

Experiment: `ORDINARY_RELATIONAL_LONG_PATH_MATURITY_FIXED_CONTINUATION_V1`

Alias in sequence: Experiment #4C

Marker: `FINAL_DEEP_MEMORY_ARCHITECTURE_CHARACTERIZATION`

Final independent audit verdict: `ACCEPT_WITH_CORRECTIONS`

Deep Memory architecture characterization: `CLOSED_FOR_THIS_EXPERIMENT_SERIES`

Is another Deep Memory architecture control required: `NO`

This note preserves the final Deep Memory architecture characterization result. It is an interpretive closeout over the authoritative #4C artifacts and independent audit corrections. It does not modify production TORMENT behavior, the #4C harness, raw result JSON, thresholds, memory behavior, or any prior preservation note.

## Central Result

Under the fixed scripted provider-free production-equivalent T1 trajectory, with compression enabled and production thresholds unchanged, an ordinary relational episode repeatedly re-entered `short_path`, underwent strength modulation through compression and reinforcement, remained age-gated until `age >= 500`, and then naturally routed through the generic `AGE_SCORE` `long_path` when `compression_score >= 0.7` and `age >= 500` coincided.

The resulting ordinary relational DeepMemory record persisted through the production DeepMemory path.

Do not generalize this result to all relational memories, typical users, typical timing, natural prevalence, optimal thresholds, provider behavior, character quality, Deep Memory usefulness, or Deep Memory harmfulness.

## Baseline And Artifacts

Baseline:

```text
HEAD == origin/main == b9fd518e53b79a69e1535ae5874bf085af55bdcd
Subject: test(lived-use): preserve relational maturity characterization
```

Authoritative harness:

```text
scripts/ordinary_relational_long_path_maturity_fixed_continuation_v1.py
SHA-256: 9169292173896ca182611b460d44499a433d4befd3b496a6c1e83b143c41d182
```

Authoritative result JSON:

```text
outputs/experiments/ordinary_relational_long_path_maturity_fixed_continuation_v1/20260811T155357Z/ordinary_relational_long_path_maturity_fixed_continuation_v1_result.json
SHA-256: 5e03c64ffc8b73ce84f5c1e81aa2b3c80be2954e5a7d9dfa398e6126ba1b39e0
```

Authoritative external workspace:

```text
C:\t\n4c11t155357z
```

Preserved evidence copy:

```text
outputs/experiments/n4c_relational_longpath_evidence/20260811T155357Z/
```

Evidence manifest:

```text
outputs/experiments/n4c_relational_longpath_evidence/20260811T155357Z/_preservation_manifest.json
SHA-256: 7767d3d605d9caa9b5aa97920f5aebaf23b30839dd8fbeea24ef877f41562469
```

Evidence verification:

```text
outputs/experiments/n4c_relational_longpath_evidence/20260811T155357Z/_preservation_verification.json
SHA-256: 60cdd840bf5528f95b3172e50cb981ffda9225418ee7be75afa9710c49e55b0c
```

The note's own SHA-256 is intentionally not embedded in this file.

## Harness Provenance Correction

The authoritative harness was finalized immediately before the authoritative run. Do not describe exact #4C harness execution as conventionally preregistered.

Allowed wording:

```text
FIXED_CONTROL_DESIGN_WITH_CONTEMPORANEOUS_AUTHORITATIVE_HARNESS
FIXED_TRAJECTORY_AND_STOP_RULE; AUTHORITATIVE_HARNESS_FINALIZED_IMMEDIATELY_BEFORE_EXECUTION
```

Earlier runs:

```text
20260811T154827Z
20260811T155135Z
```

were successful superseded-harness runs in isolated roots. Their exact harness versions are unrecoverable, so they must not be represented as independent replications. The authoritative scientific evidence is `20260811T155357Z`.

## Trajectory And Replay

Trajectory source: preserved Experiment #4 `T1_DISTINCT_EPISODES`.

First-900 SHA-256:

```text
accaaeae223f5df546b2d114afad08b7b3ba6a704d0dbd120b6c112d28ac41fd
```

First-550 SHA-256:

```text
8d4a5d0768b843097832c8d0ce338b2a082a28b7169804faf9e6a4b6ea137d47
```

Replay through #4B step 506:

```text
REPLAY_MATCH_TO_4B_THROUGH_STEP506:
INDEPENDENTLY_DEMONSTRATED
```

Do not present the harness field `first_506_byte_identical_to_4b_trajectory` as evidence by itself; it was a hardcoded literal. The independent audit established replay by raw node-history comparison: 2488 common node revisions, zero substantive mismatches after excluding four wall-clock timestamp fields.

## Step 507 Compression Event

Step `507` was an authentic production compression event:

```text
trigger: cycle_stage_change
candidates evaluated: 20
short_path: 18
exported_deep: 2
retained: 0
```

This was a genuine `EventDetector` geometric trigger. No direct compression call was experimental authority.

## Ordinary Relational AGE_SCORE Long Path

Exactly one ordinary relational `AGE_SCORE` `long_path` occurred at step 507:

```text
eid: 2
type: episode
memory_class: core
canon: false
tier: relational
born_step: 1
age: 506
pre-route strength: 0.1309
compression score: 0.7076
router cause: AGE_SCORE
route: long_path
```

Freeze:

```text
ORDINARY_RELATIONAL_SCORE_GE_0_7_AT_AGE_GE_500:
DEMONSTRATED

ORDINARY_RELATIONAL_AGE_SCORE_LONG_PATH:
DEMONSTRATED

ORDINARY_RELATIONAL_LONG_PATH_ROUTE:
AGE_SCORE

ORDINARY_RELATIONAL_LONG_PATH_COUNT_AT_STEP507:
1

FIRST_ORDINARY_RELATIONAL_LONG_PATH_EID:
2

FIRST_ORDINARY_RELATIONAL_LONG_PATH_STEP:
507

FIRST_ORDINARY_RELATIONAL_LONG_PATH_SCORE:
0.7076

FIRST_ORDINARY_RELATIONAL_LONG_PATH_AGE:
506
```

The second `long_path` at step 507 was `eid=5`, an `identity_anchor` with route cause `IDENTITY_TIER`. It was not `AGE_SCORE`.

## Both Gates Were Binding

The same event showed higher-scoring but too-young rows stayed `short_path`:

```text
eid 10: score 0.7208, age 499, short_path
eid 11: score 0.7208, age 498, short_path
eid 12: score 0.7166, age 497, short_path
```

Older-enough but score-blocked examples:

```text
eid 3: score 0.6997, age 505
eid 4: score 0.6977, age 504
eid 6: score 0.6977, age 503
eid 7: score 0.6977, age 502
eid 8: score 0.6864, age 501
eid 9: score 0.6703, age 500
```

This establishes that neither age nor score alone was sufficient.

## Short Path To Long Path

`eid=2` underwent 99 distinct `short_path` compressions from step 105 through step 506, then one `long_path` at step 507. The eid remained the same throughout.

Freeze:

```text
SAME_RELATIONAL_EID_TRANSITIONS_SHORT_PATH_TO_LONG_PATH:
DEMONSTRATED

POST_506_CODE_DERIVATION_PREDICTED_STEP507_AUTHENTIC_SCORE:
DEMONSTRATED
```

Final age-gated approach:

```text
step 501: age 500, score 0.6629, short_path
step 505: age 504, score 0.6833, short_path
step 506: age 505, score 0.6976, short_path
step 507: age 506, score 0.7076, long_path
```

Do not generalize the #4B prediction resolution beyond this deterministic replay.

## DeepMemory Text And Vector Boundary

The ordinary relational `eid=2` produced a persisted DeepMemory record:

```text
FIRST_ORDINARY_RELATIONAL_DEEPMEMORY:
DEMONSTRATED
```

The source/core summary was 364 characters. The persisted deep summary was 200 characters and equals `core_summary[:200]`; the omitted 164 characters comprised the entire assistant turn.

Freeze:

```text
DEEPMEMORY_RELATIONAL_TEXT_FULL_PRESERVATION:
CONTRADICTED
```

Do not say DeepMemory preserves the full relational episode text. This confirms the existing 200-character Deep Echo boundary on the naturally matured relational pathway.

Vector preservation differed from text preservation:

```text
source vector: private shard row 1, dim 384
deep vector: deep shard row 99, dim 384
source SHA-256: 9f2a43124571f630d1357908b30ed92addcae317d64c02eac40691a070a7921e
deep SHA-256: 9f2a43124571f630d1357908b30ed92addcae317d64c02eac40691a070a7921e
exact element equality: true
bytes identical: true
max_abs_diff: 0.0
nonzero: 384 / 384
norm: approximately 0.9999998808
```

Freeze:

```text
ORDINARY_RELATIONAL_DEEP_VECTOR_MATCHES_FULL_SOURCE_VECTOR:
DEMONSTRATED
```

The full source vector is preserved. The full source text is not. Keep this distinction explicit.

## Store-Level Retrievability

The independent audit instantiated a fresh `DeepMemoryStore` against a byte-verified scratch replica of persisted evidence.

Observed:

```text
count: 101
eid 2 recall: success
query using exact eid 2 source vector: rank 1, eid 2, cosine approximately 1.0
```

Freeze:

```text
ORDINARY_RELATIONAL_DEEPMEMORY_VECTOR_INDEXED:
DEMONSTRATED

ORDINARY_RELATIONAL_DEEPMEMORY_STORE_RETRIEVABLE:
DEMONSTRATED
```

No default Fabric/lived-use `MemoryPlan` retrieval was tested. No final rendered-surface claim is made.

## DeepMemory Accounting And Duplicate Starvation

Final authoritative store:

```text
DeepMemory text records: 101
deep map rows: 101
manifest total_rows: 101
manifest next_row: 101
nonzero deep vector rows: 101
eid 5 records: 100
eid 2 records: 1
distinct source eids: 2
```

Freeze:

```text
IDENTITY_ANCHOR_REEXPORT:
DEMONSTRATED

DEEPMEMORY_SAME_EID_DUPLICATE_RECORD_ACCUMULATION:
DEMONSTRATED
```

Engineering observation:

```text
DEEPMEMORY_DUPLICATE_VECTOR_INDEX_OCCUPANCY:
98_PERCENT_IN_THIS_RUN

DEEPMEMORY_DUPLICATE_TOPK_STARVATION:
DEMONSTRATED
```

This is not part of the `AGE_SCORE` routing claim. Do not fix it during preservation.

## Candidate Cap And Phase Split

At step 507 there were 21 eligible/scorable rows and candidate cap 20. `eid=22` had score `0.4796`, age `487`, rank `21`, and remained outside the cap. `eid=2` ranked `4`.

Freeze:

```text
CANDIDATE_CAP_NOT_MATERIAL_TO_STEP507_AGE_SCORE_RESULT:
DEMONSTRATED
```

Candidate cap remains materially relevant to the broader lifecycle observed in #4B. Do not confuse those two statements.

#4C replicated the #4B phase-duration split:

```text
early cohort born steps 1-10: score-capable under observed field regime
late cohort born steps 11-20: phase-duration penalty active, analytic ceiling approximately 0.6456

PHASE_DURATION_PENALTY_SPLIT:
REPLICATED
```

## Checkpoint And Field Issues

At step 500, `checkpoint_000500.json.tmp` exists, is approximately 972 bytes, and is truncated invalid JSON. No valid `checkpoint_000500.json` was produced.

Continuous run proceeded through steps 501, 505, 506, and 507 with no rollback, skipped compression event, or state corruption affecting this result.

Freeze:

```text
CHECKPOINT_STEP500_SERIALIZATION_WARNING:
NON_MATERIAL_TO_CONTINUOUS_4C_RESULT

DEEPMEMORY_CHECKPOINT_DURABILITY_DEFECT:
OPEN_ENGINEERING_OBSERVATION
```

`DeepMemory.compressed_step` stores `int(time.time())`, a Unix epoch, not canonical step. For `eid=2`, it therefore does not equal 507. The true export step is recoverable from the source/core node's `exported_step`.

Freeze:

```text
DEEPMEMORY_COMPRESSED_STEP_IS_EPOCH_NOT_CANONICAL_STEP:
DEMONSTRATED
```

## Configuration Freeze

```text
THRESHOLD_LOWERING:
NOT_USED

THRESHOLD_ENV_PRESENT:
{}

MANUAL_AGE_MUTATION:
NOT_USED

MANUAL_STEP_ADVANCEMENT:
NOT_USED

DIRECT_COMPRESSION_CALL_AS_AUTHORITY:
NOT_USED

MANUAL_DEEPMEMORY_EXPORT:
NOT_USED

PROVIDER:
NOT_INVOKED

CONFIGURATION_BOUNDARY:
NON_DEFAULT_COMPRESSION_ENABLED

NATURAL_PREVALENCE:
NOT_MEASURED

DEEP_MEMORY_USEFULNESS:
NOT_TESTED

DEEP_MEMORY_HARMFULNESS:
NOT_TESTED
```

## Evidence Copy

The authoritative external root was copied, not moved, from:

```text
C:\t\n4c11t155357z
```

to:

```text
outputs/experiments/n4c_relational_longpath_evidence/20260811T155357Z/
```

Verification record:

```text
file_count: 27
all_match: true
original_untouched_by_manifest_comparison: true
```

The copied evidence includes the required core files:

```text
private/nodes.jsonl
private/compression_log.jsonl
private/embeddings/manifest.json
private/embeddings/shard_000000.map.jsonl
private/embeddings/shard_000000.npy
deep_memory/memories.jsonl
deep_memory/embeddings/manifest.json
deep_memory/embeddings/shard_000000.map.jsonl
deep_memory/embeddings/shard_000000.npy
private/checkpoints/checkpoint_000500.json.tmp
index/memory_index.sqlite
```

## Closure

Known open engineering/retrieval observations remain:

1. identity-anchor repeated re-export
2. same-eid DeepMemory duplicate accumulation
3. duplicate-driven top-k starvation
4. 200-character DeepMemory text truncation
5. candidate-cap interference
6. step-500 checkpoint serialization failure
7. `DeepMemory.compressed_step` epoch/step semantic mismatch
8. default lived-use `MemoryPlan` DeepMemory headroom not characterized
9. final rendered DeepMemory surface not characterized

These observations do not authorize another architecture experiment by inertia. Future Deep Memory usefulness testing should not proceed until the text truncation and duplicate-starvation confounds are addressed.

No fix is authorized by this preservation note.
