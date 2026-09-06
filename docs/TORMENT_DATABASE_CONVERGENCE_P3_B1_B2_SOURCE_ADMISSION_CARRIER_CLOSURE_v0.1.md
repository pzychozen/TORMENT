# TORMENT Database Convergence — P3 B1/B2 Source-Admission Carrier Closure v0.1

## Verdict

```text
REAL_ROOT_P3_FIRST_ATTEMPT = STOPPED_BEFORE_FIRST_NATIVE_CHILD_WRITE
FIRST_FAILURE = P1_BOOTSTRAP_PLAN_MISUSED_AS_LEGACY_SNAPSHOT_MANIFEST
P3_REAL_ROOT_B1_B2_CARRIER_GAP = CONFIRMED
P3_B1_B2_CARRIER_REPAIR = QUALIFIED

P1_SOURCE_COPY_SEMANTICS_CHANGED = NO
LEGACY_SNAPSHOT_MANIFEST_V1_REUSED = YES
B1_SERVICE_REUSED = YES
B2_SERVICE_REUSED = YES
ROOT_B3_B4_NORMALIZER_REUSED = YES
NEW_MIGRATION_ENGINE = NO
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

The root normalizer remains the B3/B4/readiness owner.  The new P3A carrier
is a controller-invoked, maintenance-fenced composition of existing
primitives: declared frozen-source capture, `LegacySnapshotManifest` v1,
`NativeLegacyMigrationRehearsal` (B1),
`NativeMigrationRuntimeNormalizationService` (B2), and then the existing
`NativeRootWideNormalizationService` (P3B).

The P1 bootstrap plan, the P2 envelope, writer-freeze evidence, and the P2
source manifest remain distinct contracts and are not accepted as migration
snapshot manifests.  The existing snapshot validator still rejects the P1
plan with `SubstrateSnapshotManifestError` / incompatible schema version.

The carrier stores one atomic, external `p3_source_admission_carrier.json`
record.  It binds the P2 description/source-manifest digest, the operation
key, selected snapshot/manifest identities, and B1/B2 facts.  It is migration
evidence only: it carries no selector, deployment, or cutover authority.  Its
directory must be explicit and outside `data_root`.

Before a carrier is selected, the controller reconstitutes the persisted P2
envelope, requires `CUTOVER_PENDING` and `MAINTENANCE_ONLY`, and performs the
fresh P2 writer/source recheck.  Capture copies only declared present evidence
to an external snapshot, rejects link/reparse traversal, and neither mutates
legacy source nor treats a live workspace as a snapshot.

## Disposable-root qualification

The focused suite proves all of the following without a real-root read:

- P1 bootstrap-plan JSON remains an invalid snapshot manifest.
- A v1 snapshot is created, loaded, and verified before B1.
- Process loss after durable snapshot selection recovers the same snapshot
  identity; interruption after B1 resumes without duplicate source admission.
- A committed B2 whose response is lost resumes under the existing B2
  idempotency identity and then yields the same B3/B4 request.
- B3 construction requires persisted B1 and B2 facts.
- A disposable P3A → existing P3B composition closes successfully.
- An explicit empty-private scope creates no B1/B2 memory fact and no B3/B4
  request; no fake memory or vector is fabricated.
- The frozen request shape remains 154 scope inputs, 47 B3A, 25 ordinary B3B,
  3 metadata-less B3B, 0 B4A, 0 B4B, and 47 B4C.

Metadata-less Phase-9B sources stay subject to the existing per-EID qualifier;
the repair does not manufacture historical representation identity or change
the three designated `ws3`, `ws4`, and `ws5` sources.

## Operational boundary

The qualified path is not a real P3 retry.  A future retry remains separately
authorized and must supply the already-recovered successor P2 request plus an
explicit external carrier directory and the real local BGE embedder.  This
qualification does not authorize P4–P7 or alter the preserved P6 point of no
return.
