# TORMENT Memory Substrate — 7G5D1 Successor 001 Harness Failure

## Immutable successor record

This document closes, but does not alter, the consumed formal successor
`7g5d1-core-formal-successor-20260831-001`.  The successor is permanently
consumed.  It must not be rerun, reused, repaired in place, or reclassified.

| Field | Value |
| --- | --- |
| Repository HEAD | `e61c4606988b5ea69bccb8a5671394a3ba9ae4c9` |
| Administration ID | `7g5d1-core-formal-successor-20260831-001` |
| Marker path | `C:\\TORMENT\\experiments\\7g5d1_core_formal_successor_20260831_001\\.7g5d1-core-formal-successor-20260831-001.administration-started.json` |
| Marker SHA-256 | `64FA018323EF08BCD1CBA02395BF5D0FF03A17F1B0A5191C2FBE488BBD1FF26F` |
| Result path | `C:\\TORMENT\\experiments\\7g5d1_core_formal_successor_20260831_001\\result\\result.json` |
| Result SHA-256 | `A77C547BF638DB0560C08E34DC3A3F5012D5D0A1D2C1AB7B893E22E824D6B1EF` |
| Work-root SHA-256 | `e63f7dc30fc2c8f5c4b1fb4c565aec552640b91660e80d1d637780491f5e1dee` |
| Legacy HTTP event count | `8` |
| Native formal event count | `7` |
| Native router call count | `7` |
| M5 router call count | `0` |

The raw external evidence remains immutable.  This document does not copy,
edit, reformat, or regenerate its marker, result, or work-tree evidence.
Administration 001 remains immutable as well.

## Recorded outcome

```text
HARNESS_VALIDITY = EXPERIMENT_HARNESS_FAILURE
ERROR = native request contains malformed frozen storage facts
SCIENTIFIC_STORAGE_VERDICT = NOT_ESTABLISHED
SCIENTIFIC_POST_WRITE_VERDICT = NOT_ESTABLISHED
```

No scientific storage or post-write conclusion was emitted by this harness
failure.  Raw M1–M4 legacy/native activity is accounting evidence only; M5
reached no native router call, and SEQUENTIAL was not reached.

## Root cause and repair boundary

The frozen M5 storage facts truthfully state `stored = false` and
`provenance = {}`.  `formal_core_ports._facts_from_mapping()` unconditionally
called `ProvenanceV1.from_dict(...)` while constructing a full
`LegacyStorageFacingFacts` value, before `replay_no_write()` could reach the
NO_WRITE branch.  A no-write event created no stored memory and consequently
has no persisted memory provenance to provide.

```text
ROOT_CAUSE_CLASSIFICATION = FORMAL_M5_NO_WRITE_INPUT_MODEL_OVERCONSTRAINT
FIX_SCOPE = EXPERIMENT_ONLY
```

The repair must introduce a separate no-write input contract.  It must not
invent a default/synthetic `ProvenanceV1`, rewrite the frozen fixture, or
change `ProvenanceV1`, governance vocabulary, native routing, migration, B5,
or production Fabric.  The stored-event parser remains strict for stored
events.

```text
D1_CORE_FORMAL_V1 = INVALID_HARNESS_ADMINISTRATION
D1_CORE_FORMAL_SUCCESSOR_V1 = INVALID_HARNESS_ADMINISTRATION
D1_CORE_FORMAL_SUCCESSOR_002 = NOT_YET_AUTHORIZED
```
