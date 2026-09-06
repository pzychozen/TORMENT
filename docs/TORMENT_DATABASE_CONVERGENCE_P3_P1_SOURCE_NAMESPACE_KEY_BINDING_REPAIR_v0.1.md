# TORMENT Database Convergence — P3 P1 Source-Namespace Key Binding Repair v0.1

## Verdict

```text
P3_P1_SOURCE_NAMESPACE_KEY_COLLISION = CONFIRMED
P3_P1_SOURCE_NAMESPACE_KEY_BINDING_REPAIR = QUALIFIED

P1_NAMESPACE_ID_REUSED = YES
P1_NAMESPACE_KEY_REUSED = YES
P3_OPERATION_DERIVED_SOURCE_KEY_REMOVED = YES

LEGACY_SNAPSHOT_MANIFEST_V1_CHANGED = NO
B1_INVENTORY_SEMANTICS_CHANGED = NO
P1_NAMESPACE_MUTATION = NONE
P3_CHILD_PLAN_CHANGED = NO
P3_PROCESS_LOSS_RECOVERY = QUALIFIED

REAL_ROOT_CONTACT = NONE
REAL_ROOT_WRITE = NONE
REAL_P3_RETRY_EXECUTED = NO
P4_EXECUTED = NO
P5_EXECUTED = NO
P6_EXECUTED = NO
P7_EXECUTED = NO
```

## Narrow repair

P1 owns each durable `legacy_source_namespace_id` / `source_key` pair.  P3
continues to own new snapshot and artifact identities, but it no longer makes
up a source key from the P3 operation key.  Before a fresh P3 carrier creates
any snapshot directory, the source-admission service reads the exact P1
`source_key` from the already-open staging-core connection and reverse-checks
that the key resolves to the requested namespace UUID.

The snapshot manifest records that exact P1 pair.  On recovery, the carrier
record, current P1 SQLite row, scope binding UUID, and manifest must all agree
before any B1 or B2 work resumes.  Missing, empty, or contradictory mappings
refuse closed; P3 neither inserts nor repairs a P1 namespace.

## Disposable qualification

The focused suite pre-seeds canonical P1 namespace rows and proves that:

- generated v1 snapshot manifests retain the pre-existing P1 UUID and key;
- B1 reuses the namespace row without changing its count;
- a missing P1 namespace refuses before carrier or B1 mutation;
- a contradictory recovered manifest key refuses before resumed B1/B2;
- process loss after snapshot selection retains the same snapshot identity and
  P1 namespace pair;
- the prior P3A → existing P3B composition, empty-scope non-fabrication, and
  frozen 154/47/25/3/47 request shape remain closed.

No inventory rule, source grammar, representation behavior, or P1 bootstrap
artifact was changed.  A future real-root P3 retry remains separately
authorized.
