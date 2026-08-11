# TORMENT Normal And Deep Duplicate Surface Characterization V1 Result

Date: 2026-08-11

Experiment:
`NORMAL_AND_DEEP_DUPLICATE_SURFACE_CHARACTERIZATION_V1`

Subtype:
`FIRST_EXPOSURE_RETRIEVAL_CHARACTERIZATION`

## Baseline

Baseline was:

```text
HEAD == origin/main == f02bed363b256a1fe8a0083a74aab7a21a0e5263
```

Commit subject:

```text
test(lived-use): preserve deep echo fidelity characterization
```

Experiment #2 did not modify production memory code.

Configuration boundary:

```text
NON_DEFAULT_COMPRESSION_ENABLED
```

Production default remains:

```text
TORMENT_COMPRESS_ENABLE=0
```

Provider invocation:

```text
NOT_INVOKED
```

## Authoritative Run

Successful raw artifact:

```text
outputs/experiments/normal_and_deep_duplicate_surface_characterization_v1/20260811T085847Z/normal_and_deep_duplicate_surface_characterization_v1_result.json
```

Earlier historical execution provenance:

```text
outputs/experiments/normal_and_deep_duplicate_surface_characterization_v1/20260811T085806Z/
```

That earlier run failed on Windows path length before any authoritative retrieval observation. It produced no `nodes.jsonl`, no DeepMemory `memories.jsonl`, and no result JSON. It cannot contaminate the successful run.

SHA-256 identities:

```text
scripts/normal_and_deep_duplicate_surface_characterization_v1.py
06ADFD79FFB785444B4202F182B4FABBCB36049452575D5631D337868A530576

outputs/experiments/normal_and_deep_duplicate_surface_characterization_v1/20260811T085847Z/normal_and_deep_duplicate_surface_characterization_v1_result.json
AA8D23A2F9E8B6A81128D08735400A5EEA4F1979D800F70A5F67C32EC8119AFB
```

## Authentic State Construction

All eight authoritative observations used:

```text
MemoryGraph
CompressionScorer
CompressionRouter
CompressionExecutor
DeepMemoryStore
TormentFabric.query
assemble_context
```

Across 8/8 observations:

```text
router_result == long_path
source summary survived unchanged
post-long_path source strength == 0.1
DeepMemory persisted and was reloaded
```

No hand-created deep record was used. No final hit was manually inserted.

## Fresh-State Isolation

The run used eight independent workspaces/data roots. Each authoritative observation made exactly one production retrieval call.

Pre-warmth inspection was read-only and non-mutating. In every observation, the pre-warmth file was absent.

For deep-surfacing observations `O02`, `O03`, `O04`, `O06`, and `O08`, one production retrieval produced:

```text
appearance_count = 1
current_warmth = 0.2
```

For non-deep observations `O01`, `O05`, and `O07`, the warmth file remained absent.

Frozen interpretation:

```text
FIRST_EXPOSURE_WITH_NO_PRIOR_WARMTH_HISTORY
```

This is not `ZERO_WARMTH_RETRIEVAL`: newly created warmth can affect the same call after deep eligibility.

## Duplicate Co-Surface

Frozen result:

```text
SOURCE_DEEP_CO_SURFACE: DEMONSTRATED
```

For five observations, the normal source and deep derivative both survived:

```text
Fabric final hit set
structured assembled blocks
rendered context
```

This is a rendered/provider-facing duplicate surface result. It does not establish provider belief, confusion, interpretation, usefulness, or harm.

## Headroom

Frozen result:

```text
DEEP_HEADROOM_STARVATION: DEMONSTRATED
```

Controlled Q1 axis:

| Observation | top_k | deep similarity | deep gate | deep headroom | source final | deep final |
| --- | ---: | ---: | --- | ---: | --- | --- |
| O01 | 1 | approx 0.4932 | passed 0.4 | 0 | yes | no |
| O02 | 2 | approx 0.4932 | passed 0.4 | 1 | yes | yes |
| O03 | 8 | approx 0.4932 | passed 0.4 | 7 | yes | yes |

This is a causally strong single-variable demonstration of headroom starvation.

Scope caveat: `TORMENT_THINKING_ADVISORY=0` in this harness means `core_k` defaults to `top_k`. Under lived-use advisory-on behavior, the core default budget is 6, so exact numerical headroom arithmetic differs even though the same mechanism exists. Do not transfer the harness-specific headroom counts directly to advisory-on lived use.

## Shared Identity

Frozen result:

```text
STRUCTURED_SHARED_EID: DEMONSTRATED
```

The source and deep derivative carry the same logical `eid`. On all five co-surface observations, structured assembled blocks expose that same `eid`.

Therefore, a consumer of structured retrieval blocks can mechanically detect shared event identity.

## Rendered Provenance

Frozen result:

```text
RENDERED_DERIVATIVE_LINK: NOT_DEMONSTRATED
```

Rendered text exposes:

```text
[Returning Memory]
Voice
Flavor
deep textual prefix
full ordinary source text
```

Rendered text does not expose:

```text
eid
source pointer
derived-from relation
explicit statement that the Returning Memory derives from the normal block
```

The deep echo being a literal prefix of the nearby source may make the relationship inferable to a reader/provider. Inferability is not an explicit provenance claim.

## Embedding Architecture Result

Frozen result:

```text
DEEP_AND_SOURCE_SHARE_FULL_SOURCE_EMBEDDING: DEMONSTRATED
```

The source and deep records contain numerically identical embedding vector values in separate storage. Across 8/8 observations:

```text
source_similarity_to_query == deep_similarity_to_query
```

to full recorded float precision.

Production long_path exports the source row's existing embedding into `DeepMemoryStore`. The `DeepMemory.summary` field is the truncated displayed echo, but its retrieval vector represents the full source episode.

Therefore:

```text
DISPLAYED_DEEP_ECHO_INFLUENCE_ON_DEEP_RETRIEVAL:
NONE IN THIS ARCHITECTURE
```

Careful phrasing: the displayed 200-character summary is not what is indexed for deep retrieval. The tail is not separately embedded; there is one full-source-derived vector.

## Hash Embedder Boundary

The harness explicitly set:

```text
TORMENT_EMBED_PROVIDER=hash
TORMENT_HASH_DIM=384
TORMENT_HASH_SALT=normal_and_deep_duplicate_surface_characterization_v1
```

Frozen boundary:

```text
EMBEDDER:
HASH_HARNESS_SUBSTITUTE_NOT_LIVED_USE_ST_BGE
```

The ordinary companion lived-use lane uses semantic ST/BGE embeddings. `HashEmbedding` is deterministic, but it does not validate semantic meaning of the query-regime labels.

## Query-Semantic Confound

Observed similarity ordering:

| Authored regime | Similarity |
| --- | ---: |
| Q4 correction | approx 0.5988 |
| Q1 shared | approx 0.4932 |
| Q2 source-only | approx 0.4333 |
| Q6 unrelated | approx 0.4206 |
| Q5 prefix-favored | approx 0.3875 |
| Q3 broad | approx 0.1424 |

The intentionally unrelated control passed the deep `0.4` threshold while two authored related conditions scored lower.

Frozen result:

```text
QUERY_SEMANTIC_REGIME_LABELS:
NOT_VALIDATED
```

The human labels `shared`, `source-only`, `broad`, `correction`, `prefix-favored`, and `unrelated` describe authored intent, not validated semantic neighborhoods under this embedding condition. Do not derive semantic retrieval claims from their relative outcomes.

## Nonvisible Display Observation

For `O04` and `O06`:

```text
query-target fact present in full source
query-target fact absent from displayed DeepMemory.summary
deep derivative nevertheless reached final rendered context
```

Frozen descriptive observation:

```text
DEEP_SURFACED_WHILE_QUERY_TARGET_FACT_ABSENT_FROM_DISPLAYED_ECHO:
DEMONSTRATED
```

Frozen causal boundary:

```text
DEEP_RETRIEVAL_CAUSED_BY_NONVISIBLE_TAIL_EVIDENCE:
NOT_ESTABLISHED
```

Overall classification:

```text
NONVISIBLE_EVIDENCE_STATUS:
OBSERVATION_ONLY
```

Reason: the experiment observed co-occurrence, not causal contribution of the missing fact to vector similarity. The unrelated `O08` control also passed the deep gate despite the query target being absent from the source entirely.

A stronger causal claim would require a matched counterfactual using a real semantic embedder:

```text
same visible 200-character echo
same query
different full-source tail content
```

That control was not run and is not required to preserve Experiment #2's mechanical result.

## Normal-Lane Asymmetry

Frozen result:

```text
NORMAL_LANE_HAS_NO_MINIMUM_SIMILARITY_FLOOR:
DEMONSTRATED
```

The normal `MemoryGraph` retrieval path uses nearest/top-k retrieval with no `min_score` supplied on this path. In a one-memory workspace, the single source can therefore surface even for an unrelated query.

Deep retrieval, by contrast, applies its explicit `0.4` minimum similarity gate.

This explains why normal source surfacing in `O08` carries no semantic significance.

## Per-Observation Results

| Observation | Authored regime | top_k | R labels | source | deep | warmth | note |
| --- | --- | ---: | --- | --- | --- | --- | --- |
| O01 | Q1 shared | 1 | R0, R4 | yes | no | none | deep headroom starvation demonstrated |
| O02 | Q1 shared | 2 | R2, R7, R8 | yes | yes | 1 @ 0.2 | first warmth |
| O03 | Q1 shared | 8 | R2, R7, R8 | yes | yes | 1 @ 0.2 | first warmth |
| O04 | Q2 source-only | 8 | R2, R7, R8 | yes | yes | 1 @ 0.2 | query target absent from displayed echo |
| O05 | Q3 broad | 8 | R0 | yes | no | none | deep similarity below threshold |
| O06 | Q4 correction | 8 | R2, R7, R8 | yes | yes | 1 @ 0.2 | query target absent from displayed echo |
| O07 | Q5 prefix-favored | 8 | R0 | yes | no | none | deep similarity below threshold |
| O08 | Q6 unrelated | 8 | R2, R7, R8 | yes | yes | 1 @ 0.2 | proof authored semantic regime names were not validated under HashEmbedding |

## R-Label Aggregate

Exact recomputed values from measured JSON fields:

```text
R0_SOURCE_ONLY_FINAL = 3
R2_SOURCE_AND_DEEP_FINAL = 5
R4_DEEP_HEADROOM_STARVED = 1
R7_STRUCTURED_SHARED_EID = 5
R8_RENDERED_DERIVATION_NOT_EXPLICIT = 5
```

## Final Frozen Taxonomy

```text
NORMAL_AND_DEEP_DUPLICATE_SURFACE_CHARACTERIZATION_V1
FIRST_EXPOSURE_RETRIEVAL_CHARACTERIZED

SOURCE_DEEP_CO_SURFACE:
DEMONSTRATED

DEEP_HEADROOM_STARVATION:
DEMONSTRATED

STRUCTURED_SHARED_EID:
DEMONSTRATED

RENDERED_DERIVATIVE_LINK:
NOT_DEMONSTRATED

FIRST_EXPOSURE_WARMTH_MUTATION:
DEMONSTRATED

DEEP_AND_SOURCE_SHARE_FULL_SOURCE_EMBEDDING:
DEMONSTRATED

DEEP_SURFACED_WHILE_QUERY_TARGET_FACT_ABSENT_FROM_DISPLAYED_ECHO:
DEMONSTRATED

DEEP_RETRIEVAL_CAUSED_BY_NONVISIBLE_TAIL_EVIDENCE:
NOT_ESTABLISHED

NONVISIBLE_EVIDENCE_STATUS:
OBSERVATION_ONLY

NORMAL_LANE_HAS_NO_MINIMUM_SIMILARITY_FLOOR:
DEMONSTRATED

QUERY_SEMANTIC_REGIME_LABELS:
NOT_VALIDATED

EMBEDDER:
HASH_HARNESS_SUBSTITUTE_NOT_LIVED_USE_ST_BGE

PROVIDER_FALSE_CORROBORATION:
NOT_TESTED

DEEP_MEMORY_USEFULNESS:
NOT_TESTED

DEEP_MEMORY_HARMFULNESS:
NOT_TESTED

NATURAL_PREVALENCE:
NOT_MEASURED

DEFAULT_PRODUCTION_PREVALENCE:
NOT_MEASURED
```

## Statistical Boundary

These are eight engineered observations in single-memory fresh workspaces under non-default compression and a deterministic harness embedder.

They establish reachable mechanical behavior. They do not estimate rates.

Prohibited interpretations:

```text
deep duplicates occur X% of the time
unrelated queries commonly retrieve deep echoes
Deep Memory usually behaves this way
```

or any other prevalence/rate statement.

## Provider Boundary

A provider received no invocation during this experiment.

Although duplicate rendered context is demonstrated, the experiment does not establish:

```text
false corroboration
confusion
belief
misinterpretation
usefulness
harmfulness
```

## Freeze Finding

This note preserves Experiment #2 as a first-exposure retrieval characterization only.

No provider replay, semantic counterfactual, warmth-feedback experiment, retrieval fix, embedding change, threshold change, or production behavior change is authorized by this result.
