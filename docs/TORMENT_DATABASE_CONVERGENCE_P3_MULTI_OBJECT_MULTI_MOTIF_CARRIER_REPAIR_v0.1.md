# TORMENT Database Convergence — P3 Multi-Object / Multi-Motif Carrier Repair v0.1

## Scope

This qualification repairs only the external P3A source-admission carrier's
translation of already-admitted B1/B2 evidence into existing B3/B4 request
tuples. It does not change B1, B2, the root normalizer, B3A, B3B, B4A, B4B, or
B4C semantics.

## Corrected carrier law

- A `MEMORY_GRAPH` scope records every B1 object with a non-negative unique EID,
  a revision, and an allowed normalizable readiness. It requires one or more
  objects; it has no upper cardinality limit.
- B1 memory records and B2 records are deterministically EID-sorted. B2 closes
  only when its exact EID set equals B1's set.
- B3A and ordinary B3B requests are constructed once per recorded EID.
  Metadata-less B3B evidence is keyed by `(scope_key, eid)` and must exactly
  cover the admitted EID set for its unknown-identity scope.
- A declared motif-bearing scope records every valid, uniquely named motif and
  constructs one B4 request per motif on the already-selected lineage.
- Pre-B1 facts count scope shape only. Executable B3/B4 operation counts are
  independently derived from closed carrier evidence and compared to the
  constructed normalization request.

## Qualification

The disposable carrier fixture covers four deliberately out-of-order memory
EIDs and three motif IDs. It proves deterministic evidence order, four B2
facts, four B3A requests with distinct EID-specific idempotency keys, three
B4C requests with distinct identities, and recovery from a B1 transaction
committed before its carrier entry was written. The recovery keeps the original
snapshot ID, manifest, and P1 namespace pair, and replay does not duplicate
admitted objects. Empty-private, declared-empty-shared, and unmaterialized
paths remain zero-memory paths.

Focused suites passed: 79 tests across P3 source admission, root
normalization, migration normalization, representation bootstrap, reembedding
bootstrap, generalized readiness, P3 import-cycle, and post-I4 recovery.

```text
P3_SINGLE_MEMORY_SCOPE_ASSUMPTION = INVALID
P3_SINGLE_MOTIF_SCOPE_ASSUMPTION = INVALID

P3_MULTI_OBJECT_CARRIER_REPAIR = QUALIFIED
P3_MULTI_MOTIF_CARRIER_REPAIR = QUALIFIED

B1_MULTI_OBJECT_SUPPORT_CHANGED = NO
B2_MULTI_OBJECT_SUPPORT_CHANGED = NO
ROOT_NORMALIZER_MULTI_CHILD_SUPPORT_CHANGED = NO

PREMODEL_47_25_3_47_CLASSIFICATION = SCOPE_SHAPE_NOT_OPERATION_COUNTS
P3_EXACT_OPERATION_COUNTS = POST_B1_EVIDENCE_DERIVED

REAL_PARTIAL_CARRIER_RECOVERY_SHAPE = QUALIFIED

P3_B1_B2_CARRIER_REPAIR = QUALIFIED
P3_P1_SOURCE_NAMESPACE_KEY_BINDING_REPAIR = QUALIFIED
P3_MODULE_IMPORT_CYCLE_REPAIR = QUALIFIED
P3_PROCESS_LOSS_RECOVERY = QUALIFIED

REAL_ROOT_CONTACT = NONE
REAL_ROOT_WRITE = NONE
REAL_P3_RETRY_EXECUTED = NO

P4_EXECUTED = NO
P5_EXECUTED = NO
P6_EXECUTED = NO
P7_EXECUTED = NO
```
