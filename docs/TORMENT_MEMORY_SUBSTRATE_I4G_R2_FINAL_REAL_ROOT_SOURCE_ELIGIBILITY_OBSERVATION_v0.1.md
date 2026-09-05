# TORMENT Memory Substrate I4G-R2 — Final Real-Root Source-Eligibility Observation v0.1

## Status

```text
READ_ONLY_SOURCE_ELIGIBILITY_OBSERVATION
NOT_WRITER_FREEZE_EVIDENCE
NOT_ADMISSION_EVIDENCE
NO_REAL_ROOT_WRITE
NO_REAL_NORMALIZATION
NO_ACTIVATION
```

This bounded observation was made from `9b95b55d9f0cf384e894fe2a2f4a9f97e80b8a9a`
after the operator supplied `REAL_ROOT_FINAL_MINIMAL_READ_ONLY_CONTACT = YES`.
The root resolved through the existing doctrine to the expected directory:

```text
RESOLVED_REAL_ROOT = C:\TORMENT\TORMENT_repo\TORMENT-fabric_v2\torment_fabric\data
EXPECTED_REAL_ROOT_MATCH = YES
REAL_ROOT_READ_CONTACT = YES
REAL_ROOT_WRITE_CONTACT = NONE
```

Only `orchard/aria` and the three pre-named private scopes were contacted.
There was no census, owner scan, service, TormentFabric/MemoryGraph construction,
SQLite access, provider/model loading, embedding, writer operation, admission,
normalization, or activation.

## A. `orchard/aria` empty-private source posture

The identity declaration was structurally valid for `workspace_id=orchard` and
`agent_id=aria`; no unrelated identity fields are reported. The private
`nodes.jsonl` source was absent. The embedding manifest was read as structural
metadata only; no shard or vector payload was opened.

```text
ORCHARD_ARIA_IDENTITY_EVIDENCE = PRESENT_VALID
ORCHARD_ARIA_PRIVATE_DIRECTORY = PRESENT
ORCHARD_ARIA_NODES = ABSENT

ARIA_PRIVATE_EMBEDDING_MANIFEST = PRESENT
ORCHARD_ARIA_PRIVATE_TOTAL_ROWS = 0
ARIA_PRIVATE_NEXT_ROW = 0
ARIA_PRIVATE_DIMENSION = NONE
ARIA_PRIVATE_DTYPE = float32
ARIA_PRIVATE_REPRESENTATION_FIELDS = embedding_dim

ORCHARD_ARIA_MEMORY_EVENTS = ABSENT
ORCHARD_ARIA_EMPTY_PRIVATE = ELIGIBLE
ORCHARD_ARIA_PUBLIC_DISPOSITION = PUBLIC_NATIVE_EMPTY_PRIVATE
```

The zero row count and absent canonical node source mean there is no canonical
memory contradiction. An empty-private classification does not create an
agent, turn orphan material into a memory, or authorize a public runtime.

## B. bounded Phase 9B source eligibility

Only these already-named scopes were read:

```text
ws3 | PRIVATE | a1
ws4 | PRIVATE | a1
ws5 | PRIVATE | a1
```

For every scope, `nodes.jsonl` structurally parsed to the single canonical EID
`1`; there were no duplicate EIDs, missing vectors, or extra `emb_*.npy`
files. Canonical `summary`-then-`text` selection was available for the EID,
without reproducing any memory text. The `emb_1.npy` header was a valid
non-object, one-dimensional `float32` shape `(384,)` vector. Its historical
provider and model were not inspected or inferred.

```text
SCOPE                              ws3|PRIVATE|a1  ws4|PRIVATE|a1  ws5|PRIVATE|a1
nodes.jsonl present                YES             YES             YES
canonical structural parse         YES             YES             YES
canonical EIDs                     1               1               1
duplicate EIDs                     NONE            NONE            NONE
canonical text for all EIDs        YES             YES             YES
matching emb_1.npy                 YES             YES             YES
missing / extra emb_*.npy          NONE / NONE     NONE / NONE     NONE / NONE
header dtype / shape               float32 / (384,) float32 / (384,) float32 / (384,)
optional edges witness             EXPLICITLY_ABSENT EXPLICITLY_ABSENT EXPLICITLY_ABSENT
```

The existing `QualifiedMetadataLessPerEidLegacySource` helper was then used
for one direct, owner-bounded, read-only qualification per scope. It read only
its three declared locators (`nodes.jsonl`, the explicitly absent
`edges.jsonl`, and `emb_1.npy`), constructed no persistent manifest, and made
no state change. The helper's structural NPY validation did not expose vector
values. Ephemeral distinct namespace inputs were used only to exercise the
source-shape contract; they do not declare or create real-root namespaces.

```text
UNKNOWN_SCOPE_1 = ws3|PRIVATE|a1
UNKNOWN_SCOPE_1_PHASE9B_ELIGIBILITY = ELIGIBLE
UNKNOWN_SCOPE_2 = ws4|PRIVATE|a1
UNKNOWN_SCOPE_2_PHASE9B_ELIGIBILITY = ELIGIBLE
UNKNOWN_SCOPE_3 = ws5|PRIVATE|a1
UNKNOWN_SCOPE_3_PHASE9B_ELIGIBILITY = ELIGIBLE
UNKNOWN_SCOPES_ELIGIBLE_TOTAL = 3

SOURCE_REPRESENTATION_IDENTITY = UNKNOWN
UNKNOWN_PROVIDER_REMAINS_UNKNOWN = YES
UNKNOWN_MODEL_REMAINS_UNKNOWN = YES
UNKNOWN_VECTOR_RELABEL = REFUSED
CANONICAL_TEXT_AVAILABLE_FOR_ALL_UNKNOWN_EIDS = YES
UNKNOWN_REPRESENTATION_DISPOSITION = REEMBED_FROM_CANONICAL_SOURCE
TARGET = st / BAAI/bge-small-en-v1.5 / 384
```

The historical vector remains retained source evidence only. Its `float32` /
`384` header is not provider or model proof and cannot be relabeled as the
target representation.

## Provenance and readiness assessment

Static source inspection confirmed that the Phase 9B qualifier records an
UNKNOWN representation identity, an immutable source evidence identity, and
`REEMBED_REQUIRED`. Root normalization receives that source identity in
`RootRepresentationNormalizationResult.metadata_less_source_evidence_identity`,
rechecks the qualified source before dispatch, and records root normalization
completion separately. The frozen root-description contract requires the
target `st / BAAI/bge-small-en-v1.5 / 384` lane.

```text
UNKNOWN_SOURCE_PROVENANCE_EXPRESSIBLE = YES
NORMALIZATION_CLOSURE_PROVENANCE_EXPRESSIBLE = YES
```

The new observations do not contest the frozen predecessor topology results.
Together with the eligible empty-private lane and all three exact Phase 9B
source qualifications, that establishes only architectural readiness for a
separately authorized writer-freeze administration:

```text
WRITER_FREEZE_ARCHITECTURALLY_READY = YES
WRITER_FREEZE_AUTHORIZED = NO
REAL_ROOT_ADMISSION_READY = NO
REAL_ROOT_ADMISSION_AUTHORIZED = NO
REAL_ROOT_ACTIVATION_READY = NO
REAL_PRODUCTION_ACTIVATION_AUTHORIZED = NO
CLAUDE_ADVERSARIAL_REVIEW_REQUIRED = NO
```

## Boundaries retained

```text
PRODUCTION_CODE_CHANGES = 0
TEST_CHANGES = 0
TESTS_RUN = 0
SERVICE_STARTED = NO
PROVIDER_CONTACT = NONE
MODEL_LOADING = NONE
BRAINVISION_OPENED = NO
SECOND_COGNITIVE_FUNCTION_INSPECTED = NO
TORMENT_MATHEMATICS_CHANGED = NO
```

The remaining prerequisites for any later writer-freeze administration are an
explicit operator authorization naming that administration, a separately
approved immutable real-root evidence description with the actual namespace
bindings, and the independently authorized admission/normalization/activation
decisions. This observation itself supplies none of those authorities.
