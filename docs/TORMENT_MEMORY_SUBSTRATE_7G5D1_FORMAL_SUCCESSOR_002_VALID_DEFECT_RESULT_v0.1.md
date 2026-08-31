# TORMENT Memory Substrate — 7G5D1 Formal Successor-002 Valid Defect Result

## Immutable formal result

This document closes, but does not alter, the consumed formal administration
`7g5d1-core-formal-successor-20260831-002`.  It is a valid scientific result,
not a harness failure.  It must not be rerun, repaired in place, reclassified,
or used to authorize production activation.

| Field | Value |
| --- | --- |
| Repository HEAD | `2620222364442b4a57174a86411cbd80111d1207` |
| Administration ID | `7g5d1-core-formal-successor-20260831-002` |
| Marker SHA-256 | `542040DAB6752709D20C6A59E7F6181C5AC65E770D84828C9928944AE3A8A97A` |
| Result SHA-256 | `9575C37AF609FC8E651EA9D7E209A6FB465A5C41329F6AC095852ADE97C90C98` |
| Work-tree SHA-256 | `e8237a0384d2122a4ea9e98d907d3f0037b5e28ced4e0800d6354cb5069d4351` |
| Raw evidence root | `C:\\TORMENT\\experiments\\7g5d1_core_formal_successor_20260831_002` |

The marker, result, and work tree are immutable external evidence.  This
document neither copies nor changes them.

## Formal outcome

```text
HARNESS_VALIDITY = VALID
STORAGE_SUBSTRATE_VERDICT = STORAGE_SUBSTRATE_DEFECT
QUALIFIED_POST_WRITE_VERDICT = QUALIFIED_POST_WRITE_EQUIVALENT_IN_ADMINISTERED_PROFILE
```

| Arm | Storage differences |
| --- | ---: |
| M1_CREATE | 3 |
| M2_REINFORCE | 7 |
| M3_DISTINCT | 6 |
| M4_CONTRADICTION | 14 |
| M5_NO_WRITE | 0 |
| SEQUENTIAL | 23 |

M5's dedicated no-write contract passed: it emitted no storage or post-write
difference and its witness recorded no router invocation, no route witness,
no durable native-storage change, and no stored object.  All 12 native
structural witnesses validated.  Character was not administered:
`DEFERRED_PENDING_PROVENANCE_VOCABULARY` remains unchanged.

## Preserved boundaries

This valid storage-parity defect does not reopen qualified post-write, M5,
structural, Character, production-selection, dual-write, dual-read, or
cutover claims.  It establishes no production activation or cutover authority.
Any later work must be separately authorized as regression qualification of
the identified storage defects, not as a retry of D1.
