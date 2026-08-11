# TORMENT Warmth Feedback Characterization V1 Result

Date preserved: 2026-08-11

Experiment: `WARMTH_FEEDBACK_CHARACTERIZATION_V1`

Subtype: `POST_ELIGIBILITY_WARMTH_STATE_AND_COMPETITION_CHARACTERIZATION`

Status: `POST_ELIGIBILITY_WARMTH_STATE_AND_COMPETITION_CHARACTERIZED`

## Baseline And Configuration

Baseline:

```text
HEAD == origin/main == 872d95d2e30928e45bcc7dce598df3ec8758140a
Subject: test(lived-use): preserve duplicate surface characterization
```

Configuration boundary:

```text
CONFIGURATION_BOUNDARY:
NON_DEFAULT_COMPRESSION_ENABLED

Production default:
TORMENT_COMPRESS_ENABLE=0

EMBEDDER:
HASH_HARNESS_SUBSTITUTE_NOT_LIVED_USE_ST_BGE

Provider:
NOT_INVOKED

LIVED_USE_MEMORYPLAN_PATH:
NOT_EXERCISED
```

The harness used `memory_plan=None`, so `TormentFabric.query` consumed `top_k`
directly. No natural-prevalence claim, semantic-relevance claim, provider
belief claim, usefulness claim, or harmfulness claim is authorized.

## Artifacts

Harness:

```text
scripts/warmth_feedback_characterization_v1.py
```

Authoritative raw result:

```text
outputs/experiments/warmth_feedback_characterization_v1/20260811T104306Z/warmth_feedback_characterization_v1_result.json
```

Earlier failed-run directories are preserved unchanged as historical execution
provenance:

```text
20260811T104137Z:
fixture failed deep eligibility.
No warmup file existed.
No result JSON.

20260811T104233Z:
Layer A and B state existed only within that timestamped run.
Layer C died during calibration because of Windows path length.
No result JSON.
```

Each run used an independent timestamped data root. Neither failed run can
contaminate the authoritative `20260811T104306Z` run.

SHA-256 identities at preservation time:

```text
scripts/warmth_feedback_characterization_v1.py
4CD8F1C7B9DD80682B04838FDD645D958E34DA1DBA0265DF755B71E00B3DE215

outputs/experiments/warmth_feedback_characterization_v1/20260811T104306Z/warmth_feedback_characterization_v1_result.json
5D39F51F2A742E6E6D248AB7E3434BDC401D1145B46F4C0D46FD63031AA9F5C8
```

The authoritative result JSON and failed-run directories must remain immutable.

## Production Path Used

The harness used real production objects and paths:

```text
MemoryGraph
CompressionScorer
CompressionRouter
CompressionExecutor
DeepMemoryStore
TormentFabric.query
assemble_context
```

It did not manually construct DeepMemory records, assign warmth, assign
`appearance_count`, assign ranks, assign scores, inject final hits, or force a
Spirit Return mode. Warmth inspection was direct JSONL reading only; the harness
did not import or call `WarmupTracker` for observation and contained runtime
guards aborting if diagnostic inspection mutated warmth.

## Layer A: Recurrence

Measured recurrence:

```text
appearance 1 -> warmth 0.20
appearance 2 -> warmth 0.35
appearance 3 -> warmth 0.50
appearance 4 -> warmth 0.65
appearance 5 -> warmth 0.80
appearance 6 -> warmth 0.95
appearance 7 -> warmth 1.00
appearance 8 -> warmth 1.00
```

All eight Layer-A calls were deep eligible, warmed, Fabric final hits,
structured blocks, and rendered. Appearance and rendered appearance therefore
coincided in Layer A only.

Frozen outcomes:

```text
WARMTH_RECURRENCE:
DEMONSTRATED

WARMTH_CAP_AT_1_0:
DEMONSTRATED
```

The score series independently showed the cap: sub-cap 0.15 warmth increments
changed the deep score by the production-predicted amount, the 0.95 -> 1.00
increment produced the smaller exact delta, and 1.00 -> 1.00 produced zero
delta.

## Persistence Scope Correction

Do not freeze the broad label `WARMTH_PERSISTS_ACROSS_RECONSTRUCTION`.

Freeze instead:

```text
WARMTH_PERSISTS_ACROSS_SAME_PROCESS_FABRIC_RECONSTRUCTION:
DEMONSTRATED

WARMTH_IS_NOT_CACHED_ON_THE_FABRIC_OBJECT:
CODE_TRACED

FRESH_PROCESS_WARMTH_PERSISTENCE:
NOT_TESTED

SERVICE_RESTART_WARMTH_PERSISTENCE:
NOT_TESTED
```

`WarmupTracker` is created as a local variable inside `_query_deep_lane`. Each
deep-lane call constructs a tracker that reads persisted `warmup_state.jsonl`.
`TormentFabric` itself is not the holder of warmth state. Destroying and
rebuilding `TormentFabric` in the same Python process was therefore a weak
persistence test and must not be extrapolated to fresh-process or service
restart persistence.

## Window Behavior

Frozen outcomes:

```text
WINDOW_RESET_BEHAVIOR:
CODE_TRACED_NOT_EXPERIMENTALLY_CHARACTERIZED

CANONICAL_STEP_HELD_AT_ZERO_THROUGHOUT:
DEMONSTRATED
```

The `current_step - first_appearance_step > 400` reset rule was not
empirically exercised. It is not experimentally demonstrated by this run.

## Initial Eligibility Boundary

Frozen outcome:

```text
WARMTH_AFFECTS_INITIAL_DEEP_ELIGIBILITY:
CONTRADICTED
```

Warmth is downstream of:

```text
DeepMemoryStore.query
deep similarity threshold
deep headroom
source/beta filter
```

Layer C measured identical cold/warm initial deep similarity:

```text
0.9922849535942078
```

Both cold and warm conditions were initially eligible. Warmth did not increase
embedding similarity, change the deep similarity threshold, change initial deep
headroom, or rescue an ineligible deep memory.

Prohibited labels:

```text
INITIAL_ELIGIBILITY_FEEDBACK
INCREASED_EMBEDDING_SIMILARITY
DEEP_BECOMES_EASIER_TO_QUERY
```

## First-Call Same-Call Effect

Frozen outcome:

```text
FIRST_CALL_WARMTH_AFFECTS_SAME_CALL_POST_ELIGIBILITY_STATE:
DEMONSTRATED
```

Measured sequence:

```text
no prior warmth
-> deep eligible
-> first warmth = 0.20
-> same WarmupState enters Spirit Return enrichment
-> recollection strength = 0.02
-> same-call final score uses that strength
```

The first call demonstrates same-call application of the warmth floor.
Accumulated warmth effects are demonstrated by later calls.

## Layer B: Pre-Final Mutation

Preserved Layer-B causal sequence:

```text
deep similarity gate: PASS
source/beta filter: PASS
warmth: absent -> appearance_count 1 / warmth 0.20
deep Fabric final hit: YES, rank 2
deep structured block: NO
deep rendered context: NO
rendered context: empty
```

Exclusion occurred in retrieval assembly because `token_budget=1`. It was not
excluded by deep eligibility, top-k, or governance.

Frozen outcomes:

```text
WARMTH_MUTATION_REQUIRES_RENDERED_SURFACE:
CONTRADICTED

APPEARANCE_COUNT_EQUALS_RENDERED_APPEARANCE_COUNT:
CONTRADICTED
```

These two labels are derived from the same measured predicate in this harness
and are not independent corroborating evidence.

Recommended interpretive vocabulary:

```text
POST_ELIGIBILITY_DEEP_PROCESSING_COUNT
```

Definition: number of times a deep memory passed the deep-lane similarity gate
and source/beta filter and reached WarmupTracker processing. This is an
interpretive vocabulary note only; do not rename production fields.

Also freeze:

```text
WARMTH_MUTATION_PRECEDES_TOP_K_TRIM:
CODE_TRACED_NOT_EXPERIMENTALLY_ISOLATED
```

Layer B experimentally isolated mutation before rendering/assembly admission,
but not a deep candidate trimmed by unified top-k.

## Layer C: Matched Conditions

Authoritative cold condition:

```text
warmth = 0.20
deep eligibility = true
deep similarity = 0.9922849535942078
deep score = 0.9403965
deep rank = 3
rendered = false
```

Authoritative warm condition:

```text
warmth = 0.80
deep eligibility = true
deep similarity = 0.9922849535942078
deep score = 0.9582360000000001
deep rank = 2
rendered = true
```

Competitor:

```text
cold = 0.9519617072961702
warm = 0.9519543401410299
```

Spirit Return mode was `recollection` in both conditions. No mode transition
occurred.

Frozen outcome:

```text
SPIRIT_RETURN_MODE_TRANSITION_EFFECT:
NOT_TESTED
```

The measured effect is within-mode recollection strength amplification.

## Legitimate Warming And Source Control

The warm condition reached warmth 0.80 through legitimate prior production
retrievals only. Warmth and `appearance_count` were never manually set.

Before the authoritative probe, cold/warm target source states were matched on:

```text
summary
strength
embedding digest
created timestamp
last reinforcement
compression metadata
```

Competitor states were matched equivalently. Canonical step remained 0
throughout. SRG was disabled. Source rows were not reinforced by warming
retrievals.

## Competitor Drift

Measured competitor drift:

```text
cold: 0.9519617072961702
warm: 0.9519543401410299
absolute difference: 7.367155140380888e-06
```

Cause: exactly one second of wall-clock time between cold and warm probes.
Private `MemoryGraph.search` applies half-life decay:

```text
0.5^(1 / 86400)
```

for one second at one-day half-life. The measured warm/cold similarity ratio
matched that factor. Undecayed raw cosine values were bit-identical between
conditions, and `score_hit` reproduced both competitor scores from recorded
production explain inputs.

The wall-clock drift moved the competitor slightly down in the warm condition,
in the same direction as the reported rank flip. However, the deep warmth delta
was:

```text
0.0178395
```

which is approximately 2421 times larger than competitor drift. Removing
competitor drift completely still leaves the warm deep hit above the cold
competitor by approximately:

```text
0.0062743
```

Competitor drift cannot explain the flip.

## Deep Score Mechanism

Frozen outcome:

```text
WARMTH_CHANGES_FINAL_SCORE:
DEMONSTRATED
```

Measured:

```text
cold deep score: 0.9403965
warm deep score: 0.9582360000000001
delta: 0.01783950000000012
```

All relevant score inputs were identical except warmth and deterministic
downstream `strength`:

```text
sim = 0.8495
recency_days = 0.0
motif_alignment = 0.0
contradiction_risk = 0.0
continuity/type bonus = 0.0
Spirit Return mode = recollection
```

Strength:

```text
cold: 0.1 * 0.20 = 0.02
warm: 0.1 * 0.80 = 0.08
```

Production formula prediction:

```text
0.8495 * 0.35 * 0.1 * (0.8 - 0.2)
= approximately 0.0178395
```

The measured scores reproduced the production formula to practical float
equality.

Frozen outcome:

```text
MEASURED_DELTA_EQUALS_PRODUCTION_FORMULA_PREDICTION:
DEMONSTRATED
```

## Structural Score Asymmetries

Frozen measured structural findings:

```text
DEEP_HIT_SIM_INPUT_IS_COMPRESSION_SCORE_NOT_QUERY_SIMILARITY:
DEMONSTRATED

DEEP_HIT_RECENCY_DAYS_IS_ZERO:
DEMONSTRATED

DEEP_HIT_RECEIVES_NO_CONTINUITY_BONUS:
DEMONSTRATED

PRIVATE_LANE_SIM_CARRIES_WALLCLOCK_HALF_LIFE_DECAY:
DEMONSTRATED
```

For final unified scoring, the deep hit's `sim` field was the stored
compression score:

```text
0.8495
```

The embedding similarity:

```text
0.9922849535942078
```

was used to enter the deep lane, not as final unified-score `sim`.

Deep Spirit Return hits omitted `created_ts` on this path, causing unified
scoring to fall back to current `now_ts` and produce `recency_days=0.0`.
Private source hits received continuity adjustment `+0.14` in Layer C. Deep hits
received `0.0`.

These are structural findings observed in this controlled path. Do not
generalize beyond the characterized path without further evidence.

## Final Rank

Frozen outcome:

```text
WARMTH_CHANGES_FINAL_RANK:
DEMONSTRATED
```

Production final ordering:

```text
COLD:
rank 1 target source ~1.26563
rank 2 competitor ~0.951962
rank 3 target deep 0.9403965

WARM:
rank 1 target source ~1.26562
rank 2 target deep 0.958236
rank 3 competitor ~0.951954
```

The target source remained rank 1 in both conditions.

Prohibited label:

```text
WARM_MEMORIES_CROWD_OUT_CORE_MEMORIES
```

This experiment did not demonstrate that.

## Surface Flip Qualification

Do not freeze the broad label `WARMTH_FLIPS_FINAL_SURFACE_OUTCOME` without
qualification.

Freeze instead:

```text
WARMTH_FLIPS_FINAL_SURFACE_OUTCOME_UNDER_CONTEXT_BUDGET_CONTENTION:
DEMONSTRATED
```

Authoritative budget:

```text
188 tokens
```

Under the companion assembler:

```text
situational hard cap = 74 tokens
deep block = 74 tokens
competitor block = 15 tokens
```

The engineered cap could admit only one of them after ordering.

```text
COLD:
competitor ranked before deep
competitor selected
deep excluded by situational block cap

WARM:
deep ranked before competitor
deep selected
competitor excluded by situational block cap
```

This establishes a post-ranking context-survival flip under context-budget
contention.

## Generous-Budget Negative Control

The existing `layers.C.budget_probe` result is promoted from scaffolding to a
frozen reported result.

At `token_budget=4000`, with the same relevant fixtures and warmth conditions:

```text
cold deep rank = 3
warm deep rank = 2
cold deep rendered = true
warm deep rendered = true
```

Frozen outcome:

```text
WARMTH_FLIPS_SURFACE_AT_GENEROUS_CONTEXT_BUDGET:
CONTRADICTED
```

The surface flip is budget-contingent. The rank effect persists at generous
budget; the rendered inclusion effect does not.

## Engineered Design Disclosure

Frozen outcomes:

```text
COMPETITOR_SELECTED_BY_FLIP_SEEKING_CALIBRATION_GRID:
ENGINEERED_BY_DESIGN

CONTEXT_BUDGET_ENGINEERED_TO_ADMIT_ONE_SITUATIONAL_BLOCK:
ENGINEERED_BY_DESIGN
```

Calibration examined 66 candidate settings. Three produced the desired
score-order flip. One was selected and then re-created in fresh authoritative
cold/warm workspaces. This is legitimate boundary-finding and existence-proof
construction. It is not frequency evidence.

The 188-token budget was computed from block sizes to create a one-block
contention condition. Do not present the surface flip as naturally encountered
prevalence.

## Harness Defects And Scope Notes

Harness note A:

```text
WARMTH_MUTATION_REQUIRES_RENDERED_SURFACE
APPEARANCE_COUNT_EQUALS_RENDERED_APPEARANCE_COUNT
```

used byte-identical predicates. They are not independent evidence.

Harness note B:

```text
competitor_initial_eligibility
```

is a vacuous harness field because `x or {}` is never `None`. Do not use that
field as evidence. The competitor's actual presence and ranks independently
establish the substantive result.

Harness note C:

The harness-side deep eligibility diagnostic models production headroom for
`memory_plan=None` and is correct for this run. It should not be reused blindly
for non-null MemoryPlan behavior.

## Feedback Result

Strongest allowed claim:

```text
POST_ELIGIBILITY_RETRIEVAL_FEEDBACK:
DEMONSTRATED
```

Meaning:

```text
deep passes initial eligibility
-> warmth is mutated
-> recollection strength increases
-> final unified score increases
-> final rank changes
-> under engineered context-budget contention, downstream context survival changes
```

This is not:

```text
GLOBAL_RETRIEVAL_ATTRACTOR
INITIAL_ELIGIBILITY_FEEDBACK
INCREASED_EMBEDDING_SIMILARITY
DEEP_BECOMES_EASIER_TO_QUERY
WARMTH_INCREASES_DEEP_RELEVANCE
```

Also freeze:

```text
WARMTH_CAN_CHANGE_A_FUTURE_POST_ELIGIBILITY_SURFACE_OUTCOME:
DEMONSTRATED

FUTURE_SURFACING_PROBABILITY_INCREASE:
NOT_MEASURED
```

One deterministic engineered instance is not a probability estimate.

## Final Frozen Taxonomy

```text
WARMTH_FEEDBACK_CHARACTERIZATION_V1

POST_ELIGIBILITY_WARMTH_STATE_AND_COMPETITION_CHARACTERIZED

WARMTH_RECURRENCE:
DEMONSTRATED

WARMTH_CAP_AT_1_0:
DEMONSTRATED

WARMTH_PERSISTS_ACROSS_SAME_PROCESS_FABRIC_RECONSTRUCTION:
DEMONSTRATED

WARMTH_IS_NOT_CACHED_ON_THE_FABRIC_OBJECT:
CODE_TRACED

FRESH_PROCESS_WARMTH_PERSISTENCE:
NOT_TESTED

SERVICE_RESTART_WARMTH_PERSISTENCE:
NOT_TESTED

WINDOW_RESET_BEHAVIOR:
CODE_TRACED_NOT_EXPERIMENTALLY_CHARACTERIZED

CANONICAL_STEP_HELD_AT_ZERO_THROUGHOUT:
DEMONSTRATED

WARMTH_AFFECTS_INITIAL_DEEP_ELIGIBILITY:
CONTRADICTED

FIRST_CALL_WARMTH_AFFECTS_SAME_CALL_POST_ELIGIBILITY_STATE:
DEMONSTRATED

WARMTH_MUTATION_REQUIRES_RENDERED_SURFACE:
CONTRADICTED

APPEARANCE_COUNT_EQUALS_RENDERED_APPEARANCE_COUNT:
CONTRADICTED
[same underlying measurement; not independent corroboration]

WARMTH_MUTATION_PRECEDES_TOP_K_TRIM:
CODE_TRACED_NOT_EXPERIMENTALLY_ISOLATED

WARMTH_CHANGES_FINAL_SCORE:
DEMONSTRATED

WARMTH_CHANGES_FINAL_RANK:
DEMONSTRATED

WARMTH_FLIPS_FINAL_SURFACE_OUTCOME_UNDER_CONTEXT_BUDGET_CONTENTION:
DEMONSTRATED

WARMTH_FLIPS_SURFACE_AT_GENEROUS_CONTEXT_BUDGET:
CONTRADICTED

POST_ELIGIBILITY_RETRIEVAL_FEEDBACK:
DEMONSTRATED

WARMTH_CAN_CHANGE_A_FUTURE_POST_ELIGIBILITY_SURFACE_OUTCOME:
DEMONSTRATED

MEASURED_DELTA_EQUALS_PRODUCTION_FORMULA_PREDICTION:
DEMONSTRATED

DEEP_HIT_SIM_INPUT_IS_COMPRESSION_SCORE_NOT_QUERY_SIMILARITY:
DEMONSTRATED

DEEP_HIT_RECENCY_DAYS_IS_ZERO:
DEMONSTRATED

DEEP_HIT_RECEIVES_NO_CONTINUITY_BONUS:
DEMONSTRATED

PRIVATE_LANE_SIM_CARRIES_WALLCLOCK_HALF_LIFE_DECAY:
DEMONSTRATED

COMPETITOR_SELECTED_BY_FLIP_SEEKING_CALIBRATION_GRID:
ENGINEERED_BY_DESIGN

CONTEXT_BUDGET_ENGINEERED_TO_ADMIT_ONE_SITUATIONAL_BLOCK:
ENGINEERED_BY_DESIGN

SPIRIT_RETURN_MODE_TRANSITION_EFFECT:
NOT_TESTED

EMBEDDER:
HASH_HARNESS_SUBSTITUTE_NOT_LIVED_USE_ST_BGE

LIVED_USE_MEMORYPLAN_PATH:
NOT_EXERCISED

CONFIGURATION_BOUNDARY:
NON_DEFAULT_COMPRESSION_ENABLED

FUTURE_SURFACING_PROBABILITY_INCREASE:
NOT_MEASURED

PROVIDER_BEHAVIOR:
NOT_TESTED

DEEP_MEMORY_USEFULNESS:
NOT_TESTED

DEEP_MEMORY_HARMFULNESS:
NOT_TESTED

NATURAL_PREVALENCE:
NOT_MEASURED
```

## Interpretive Boundary

Explicitly prohibited:

```text
GLOBAL_RETRIEVAL_ATTRACTOR
INITIAL_ELIGIBILITY_FEEDBACK
INCREASED_EMBEDDING_SIMILARITY
DEEP_BECOMES_EASIER_TO_QUERY
WARMTH_INCREASES_DEEP_RELEVANCE
WARM_MEMORIES_CROWD_OUT_CORE_MEMORIES
INCREASED_PROBABILITY_OF_FUTURE_SURFACING
provider belief/confusion
Deep Memory usefulness/harmfulness
natural prevalence
default-production prevalence
```

Experiment #3 establishes a bounded mechanical post-eligibility feedback
mechanism only.
