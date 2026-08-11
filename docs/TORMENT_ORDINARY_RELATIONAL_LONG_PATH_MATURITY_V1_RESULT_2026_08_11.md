# TORMENT Ordinary Relational Long Path Maturity V1 Result

Preservation date: 2026-08-11

Experiment: `ORDINARY_RELATIONAL_LONG_PATH_MATURITY_V1`

Alias in sequence: Experiment #4B

Result marker: `INTERMEDIATE_RESULT_REQUIRES_FIXED_CONTINUATION_CONTROL`

Final audit verdict: `REDESIGN_OR_ADD_CONTROL_OPTION_B`

This note preserves Experiment #4B as an intermediate characterization result. #4B is not failed. It established ordinary relational maturation mechanics under the fixed scripted production-equivalent trajectory, but its predeclared three-post-age500-event stop rule right-censored the unresolved strength cycle at step 506.

Do not describe this result as demonstrating that ordinary relational memories do not reach DeepMemory.

## Baseline And Artifacts

Baseline:

```text
HEAD == origin/main == 9dc346fff2f92ded5b3a72973e791e78ee103a8d
Subject: test(lived-use): preserve M6 short-root confirmation
```

Harness:

```text
scripts/ordinary_relational_long_path_maturity_v1.py
```

Authoritative result JSON:

```text
outputs/experiments/ordinary_relational_long_path_maturity_v1/20260811T150017Z/ordinary_relational_long_path_maturity_v1_result.json
```

External authoritative workspace:

```text
C:\t\n4b11t150017z
```

Configuration boundary: `NON_DEFAULT_COMPRESSION_ENABLED`

Provider: `NOT_INVOKED`

Embedder: `ST / BAAI/bge-small-en-v1.5`

Transport boundary: `IN_PROCESS_ENDPOINT_EQUIVALENT_LIVED_USE_PATH`

No production code, harness code, threshold, raw result JSON, or memory behavior was modified during preservation.

## Trajectory

Preserved source: Experiment #4 `T1_DISTINCT_EPISODES`

Selected exchanges: first 900

Canonical trajectory SHA-256:

```text
accaaeae223f5df546b2d114afad08b7b3ba6a704d0dbd120b6c112d28ac41fd
```

First 105 exchanges byte-identical to the original T1 generator: `DEMONSTRATED`

No adaptive trajectory edits were made.

Freeze:

```text
TRAJECTORY_RIGHT_CENSORED_AT_STEP_506:
DEMONSTRATED

ORDINARY_RELATIONAL_LONG_PATH:
NOT_DEMONSTRATED_THROUGH_STEP_506

ORDINARY_RELATIONAL_AGE_SCORE_LONG_PATH:
NOT_DEMONSTRATED_AND_NOT_EXCLUDED
```

## Target Cohort

Target cohort: 20 ordinary relational episodes:

```text
2,3,4,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22
```

All target rows were `type=episode`, `memory_class=core`, `canon=false`, and `tier=relational`.

Automatic background rows were excluded from the target cohort:

```text
seed_canon eid 1
identity_anchor eid 5
```

## Compression Events

Observed authentic production compression events: 99

Triggers:

```text
68 corridor_exit
31 cycle_stage_change
```

Every event evaluated 20 candidates and produced:

```text
19 short_path relational mutations
1 long_path identity_anchor export
```

Relational observations:

```text
selected: 1881
outside candidate cap: 99
```

Freeze:

```text
SHORT_PATH_REENTRY_OBSERVED:
DEMONSTRATED

MULTIPLE_SHORT_PATH_PASSES_ON_SAME_RELATIONAL_EID:
DEMONSTRATED
```

Nineteen relational eids were short-pathed on all 99 events. `compressed=true` does not exclude later compression candidacy.

## Relational Strength And Score Mechanics

Critical correction: relational short_path mutation used:

```text
TORMENT_COMPRESS_RELATIONAL_MULT = 0.7
```

not:

```text
TORMENT_COMPRESS_SHORT_STRENGTH_MULT = 0.5
```

Observed formula:

```text
new_strength = round(max(0.05, old_strength * 0.7), 4)
```

Verified: 1881 / 1881 mutations, zero mismatches.

Freeze:

```text
RELATIONAL_SHORT_PATH_MULTIPLIER:
0.7_NOT_0.5
```

Observed reinforcement restoration:

```text
new_strength = round(0.7 * old_strength + 0.3, 4)
```

Verified: 381 / 381 reinforcement transitions, zero mismatches.

Freeze:

```text
REINFORCEMENT_STRENGTH_RESTORATION:
s -> 0.7s + 0.3
```

For this trajectory, production fields reduced exactly to:

```text
score = 0.731 - 0.1785 * strength
```

With sustained >=10 penalty:

```text
score = 0.6545 - 0.1785 * strength
```

Verified: 1881 / 1881 score records, zero mismatches.

Freeze:

```text
RELATIONAL_COMPRESSION_SCORE_CLOSED_FORM:
DEMONSTRATED

RELATIONAL_SCORE_ANALYTIC_CEILING_NO_PENALTY:
0.7221

SCORE_0_7_CROSSING_STRENGTH:
0.173669
```

Age contributed no positive score term. Age was a separate router gate.

## Phase-Duration Penalty

The sustained value:

```text
max(phase_duration_steps, corridor_duration_steps)
```

was effectively a birth-time snapshot for this cohort.

Rows born at steps 1-10 had no phase-duration penalty, analytic ceiling 0.7221, and score 0.7 was structurally reachable.

Rows born at steps 11-20 had the phase-duration penalty active, analytic ceiling approximately 0.6456, and score 0.7 was structurally unreachable in the observed lifecycle.

Freeze:

```text
PHASE_DURATION_PENALTY_BLOCKS_10_OF_20_COHORT_ROWS:
DEMONSTRATED

RELATIONAL_SCORE_0_7_MATHEMATICALLY_REACHABLE:
YES_FOR_ROWS_BORN_BEFORE_PHASE_DURATION_10
```

Do not generalize this beyond the traced field regime.

## Two-Process Strength Race

Freeze:

```text
SHORT_PATH_WEAKENING_RAISES_IMMEDIATE_NEXT_RELATIONAL_SCORE:
DEMONSTRATED

SHORT_PATH_WEAKENING_MONOTONICALLY_MATURES_A_ROW_ACROSS_REINFORCEMENT:
CONTRADICTED

RELATIONAL_COMPRESSIBILITY_IS_A_TWO_PROCESS_RACE_ON_STRENGTH:
DEMONSTRATED
```

Short_path lowered strength and increased compression score. Reinforcement raised strength and lowered compression score. For all 1881 scored records, `retrieval_resist=0`, `basin_resist=0`, `tension_resist=0`, and `z_score=0.65`; the observed score oscillation was driven entirely by strength.

## Score Gate And Age Gate

First relational score >=0.7:

```text
eid: 2
step: 118
age: 117
score: 0.7016
```

Global observed maximum:

```text
eid: 3
step: 321
age: 319
strength: 0.05
score: 0.7221
```

Freeze:

```text
RELATIONAL_SCORE_GE_0_7_BEFORE_AGE500:
DEMONSTRATED
```

The AGE_SCORE long_path did not fire at those score crossings because age was below 500.

First target age500:

```text
eid: 2
step: 501
age: 500
```

Post-age500 authentic events:

```text
501: max score 0.6629
505: max score 0.6833
506: max score 0.6976
```

Freeze:

```text
AGE_500_GATE_REACHED_BY_ORDINARY_RELATIONAL_ROW:
DEMONSTRATED

POST_AGE500_AUTHENTIC_COMPRESSION_OPPORTUNITY:
DEMONSTRATED
```

Corrected preservation wording:

```text
RELATIONAL_SCORE_GE_0_7_AT_AGE_GE_500:
NOT_OBSERVED_IN_THREE_REFRACTORY_PHASE_EVENTS
```

The raw historical JSON classifier wording is not rewritten.

## Stop-Rule Censoring

At step 501, eid 2 was reinforced:

```text
strength -> 0.3816
```

Its next authentic event sequence:

```text
501: pre-strength 0.3816, score 0.6629
505: pre-strength 0.2671, score 0.6833
506: pre-strength 0.1870, score 0.6976
post-506 strength: 0.1309
```

Read-only diagnostic at the persisted post-506 state:

```text
score: 0.7076
age: 505
```

This is:

```text
POST_EVENT_CODE_REDERIVED_DIAGNOSTIC_NOT_AN_AUTHENTIC_NEXT_COMPRESSION_EVENT
```

Do not claim M9 from it.

Freeze:

```text
POST_506_DIAGNOSTIC_EID2:
0.7076_CODE_REDERIVED_NOT_AN_EVENT

STOP_RULE_CENSORED_UNRESOLVED_TRAJECTORY:
DEMONSTRATED
```

The crossing-strength arithmetic required the fourth event after the step-501 reinforcement. The stop rule allowed three.

## Right Censoring

At stop step 506:

```text
6 / 20 target rows had reached age500
14 / 20 target rows had not reached age500
```

Among the 10 score-capable rows, 6 had reached age500 and 4 were still right-censored:

```text
eid 9 -> age500 step 507
eid 10 -> age500 step 508
eid 11 -> age500 step 509
eid 12 -> age500 step 510
```

Their post-506 diagnostic scores were approximately:

```text
0.7208
0.7208
0.7208
0.7166
```

Freeze:

```text
COHORT_RIGHT_CENSORED:
14_OF_20_NEVER_REACHED_AGE500

SCORE_CAPABLE_COHORT_RIGHT_CENSORED:
4_OF_10
```

## Candidate Cap

Production candidate cap: 20

Scorable rows: 21

Protected seed_canon was excluded. Identity anchor eid 5 was a candidate at every event. The relational cohort contained 20 rows.

Observed:

```text
19 relational selected every event
eid 22 rank 21 / outside cap every event
```

Eid 22:

```text
born_step: 20
strength: 0.98 throughout
diagnostic score: 0.4796
outside cap: 99 / 99
never compressed
age at stop: 486
age500 would occur at step 520
```

Freeze:

```text
CANDIDATE_CAP_MATERIAL_TO_RELATIONAL_SURVIVAL:
DEMONSTRATED

CANDIDATE_CAP_SHIELDS_RELATIONAL_ROW_FROM_SHORT_PATH:
DEMONSTRATED

CANDIDATE_CAP_EXCLUSION_IS_SELF_REINFORCING:
DEMONSTRATED

CANDIDATE_CAP_SURVIVOR_REACHED_AGE500:
NO
```

Do not claim what eid 22 would do after age500.

## Identity Re-Export

Background identity anchor eid: 5

Observed:

```text
exports: 99
re-exports: 98
Deep textual records: 99, all eid 5, one distinct summary
Deep embedding/vector rows: 99, all eid 5
deduplication: not observed
```

Freeze:

```text
EXPORTED_DEEP_SOURCE_RECOMPRESSION:
DEMONSTRATED

IDENTITY_ANCHOR_REEXPORT:
DEMONSTRATED

DEEPMEMORY_SAME_EID_DUPLICATE_RECORD_ACCUMULATION:
DEMONSTRATED
```

Identity anchor score after first export was approximately 0.5873. Eid 22 score was 0.4796. Therefore the identity anchor occupied the marginal 20th candidate slot on every event.

Freeze:

```text
IDENTITY_REEXPORT_CONSUMES_CANDIDATE_CAP_SLOT:
DEMONSTRATED

IDENTITY_REEXPORT_MATERIAL_TO_RELATIONAL_CANDIDATE_CAP:
DEMONSTRATED
```

This is a background architecture observation. Do not fix it in this preservation step.

## Operational Warnings

Checkpoint warning:

```text
CHECKPOINT_STEP500_SERIALIZATION_WARNING:
NON_MATERIAL_TO_CONTINUOUS_RUN
```

At step 500, checkpoint serialization attempted to serialize numpy ndarray state and failed, leaving `private/checkpoints/checkpoint_000500.json.tmp` at approximately 972 bytes with truncated JSON and no final `checkpoint_000500.json`. The error was caught; steps 501-506 continued; there was no graph rollback, skipped compression event, or lost step.

Do not resume this workspace for #4C. Do not fix the checkpoint issue in this experiment.

`PACKET-GATE` / `PACKET-BLOCKED` logs came from intentionally disabled hivemind functionality and had no material effect on private relational compression.

## Secure Findings

Preserve as secure:

```text
short-path reentry
99 repeated passes on 19 relational rows
score>=0.7 naturally reachable before age500
analytic score formula
strength-only oscillation
age500 reached
three authentic post-age500 events
no AGE_SCORE long_path through step506
candidate-cap survivor
phase-duration penalty split
identity re-export duplication
identity/candidate-cap interaction
checkpoint warning non-material
```

## Unresolved Findings

Preserve as unresolved:

```text
ORDINARY_RELATIONAL_LONG_PATH_MATURITY_OVER_FULL_PREREGISTERED_TRAJECTORY:
UNRESOLVED

ORDINARY_RELATIONAL_AGE_SCORE_LONG_PATH:
NOT_DEMONSTRATED_AND_NOT_EXCLUDED

CANDIDATE_CAP_SURVIVOR_AT_AGE500:
NOT_TESTED

FOUR_SCORE_CAPABLE_ROWS_AGING_IN_AT_507_TO_510:
NOT_OBSERVED
```

## External Evidence Preservation

The external authoritative workspace was copied byte-for-byte, without moving or modifying `C:\t\n4b11t150017z`.

Evidence copy root:

```text
outputs/experiments/n4b_relational_maturity_evidence/20260811T150017Z/external_workspace
```

Manifest:

```text
outputs/experiments/n4b_relational_maturity_evidence/20260811T150017Z/external_workspace_manifest.jsonl
```

Verification record:

```text
outputs/experiments/n4b_relational_maturity_evidence/20260811T150017Z/external_workspace_verification.json
```

Preservation verification:

```text
source_file_count: 27
copy_file_count: 27
manifest_file_count: 27
all_match: true
manifest_sha256: 75c883c3ecf84ed4eb81ec1dcf42faa451920b20e3ea1669a0cb9b84b91d83f3
verification_sha256: e003c0f88dd8e2a3bfeb4f61b8954ba3530428b463c46634f7f0908329a5252e
```

Especially preserved:

```text
private/compression_log.jsonl
private/nodes.jsonl
private/embeddings/manifest.json
private/embeddings/shard_000000.map.jsonl
private/embeddings/shard_000000.npy
deep_memory/memories.jsonl
deep_memory/embeddings/manifest.json
deep_memory/embeddings/shard_000000.map.jsonl
deep_memory/embeddings/shard_000000.npy
private/checkpoints/checkpoint_000500.json.tmp
```

## Artifact Hashes

```text
harness:
1b03eea14d64f4799262896b0902231be868db4bd4c4a6932b2375dfb6b7960e

authoritative result JSON:
8a4d4595351cbdf27e7e61273f0dc851ac3b44ddc524a79498e4f1086bcaedc6

evidence manifest:
75c883c3ecf84ed4eb81ec1dcf42faa451920b20e3ea1669a0cb9b84b91d83f3

evidence verification record:
e003c0f88dd8e2a3bfeb4f61b8954ba3530428b463c46634f7f0908329a5252e
```

The preservation note hash is computed externally after file creation.

## Continuation Boundary

Do not rerun #4B from this note. Do not run #4C yet. A fixed continuation control is required before treating the ordinary relational AGE_SCORE route as resolved.
