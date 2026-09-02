# Blocker-5 A5R0 — Immutable admission identity / pending compatibility

## Result

B5-A5R0 repairs the B5-A2/A3 binding collision without opening B5-A5. The multi-scope descriptor remains mutable progress evidence: snapshots, core identity, B2/B3A/B4A/B5 results, and final completion facts still change its ordinary full digest.

The selector/core field historically named `descriptor_digest` now carries the immutable `admission_identity_digest` for R0-prepared admissions. No selector SQLite migration or native-core DDL change was needed.

The selector's read-only preflight now treats a missing data root as empty
pre-selector authority and does not create it. This preserves ordinary first
legacy startup, where Fabric owns initial root creation.

```text
B5_A5R0_ADMISSION_IDENTITY_REPAIR          = QUALIFIED
IMMUTABLE_ADMISSION_IDENTITY                = QUALIFIED
ADMISSION_IDENTITY_DIGEST_STABLE            = YES
MUTABLE_DESCRIPTOR_PROGRESS_PRESERVED       = YES
DEPLOYMENT_DESCRIPTOR_BINDING               = ADMISSION_IDENTITY_DIGEST
FINAL_COMPLETED_DESCRIPTOR_VERIFICATION     = REQUIRED
ADMISSION_CORE_STATE_LAW_CHANGED            = NO
SELECTOR_SCHEMA_CHANGED                      = NO
NATIVE_CORE_SCHEMA_CHANGED                   = NO
REAL_PRODUCTION_CUTOVER_PERFORMED            = NO
KERNEL_FILES_CHANGED                         = 0
```

Historical complete B5-A2/A3 descriptors without an R0 identity retain their full-descriptor binding, but cannot model pending-before-admission operation.

## Preparation and identity contract

`ExistingWorkspaceNativeMultiScopeAdmissionService.prepare()` is bounded P1. It validates topology, freezes lane snapshots/manifests, creates or recovers the inert core and namespaces, and freezes the core UUID and identity. It cannot run B2, B3A, B4A, or B5.

The result has the core path/UUID, descriptor digest, identity digest, and per-lane snapshot witnesses. Exact retry recovers identical facts; changed request, manifest, or source fingerprint refuses. The source fingerprint is checked again immediately before the identity is frozen.

Identity binds contract/schema, workspace and operation identity, source fingerprint, core UUID/path, lane plans and namespaces, representation lane, unknown scope, embedder, feature/post-write posture, retained-owner evidence, and snapshot/manifest IDs and digests. It excludes mutable progress.

```text
PREPARED_STAGING_CORE_HAS_PRODUCTION_AUTHORITY = NO
```

## Pending / completion / active law

```text
P0 writers drained
P1 prepare snapshots + inert STAGING/LEGACY_ACTIVE core + stable identity
P2 external LEGACY_ACTIVE -> CUTOVER_PENDING(identity digest)
P3 run/resume existing B2/B3A/B4A/B5 on STAGING/LEGACY_ACTIVE core
P4 descriptor ADMISSION_COMPLETE + immutable completion witness
P5 core -> STAGING/CUTOVER_PENDING
P6 core -> ACTIVE_CORE/NATIVE_ACTIVE, recording completion witness
P7 external selector -> NATIVE_ACTIVE last
```

The original inert binding still rejects any non-`STAGING + LEGACY_ACTIVE` core. External pending is the public fence while semantic admission runs.

At B5, the descriptor creates a non-self-referential completion witness. It binds the identity, selected qualified-profile digest, core UUID, whole-workspace closure, and every completed descriptor fact except itself. Activation requires that same profile digest as its selected predecessor, receives the current full descriptor digest, and records the receipt in existing `maintenance_events`. No core DDL was added.

Each B5-A3 owner recovery requires exact selector/core identity, a current `ADMISSION_COMPLETE` descriptor, valid completion and activation evidence, and matching core UUID/profile/lane/SQLite runtime. Incomplete, regressed, or tampered descriptors refuse native ownership without legacy fallback.

```text
ADMISSION_UNDER_EXTERNAL_PENDING             = QUALIFIED
CORE_REMAINS_LEGACY_ACTIVE_DURING_ADMISSION  = YES
PUBLIC_SERVICE_DURING_EXTERNAL_PENDING       = REFUSED
DUAL_WRITE_WINDOW                            = NONE
DUAL_READ_AUTHORITY_WINDOW                   = NONE
```

## Crash/restart implication

`C0.5` is lawful: after P1 and before P2, legacy may restart because snapshots and the staging core are inert and semantic native admission did not occur. From P2 through P6, the resolver is `MAINTENANCE_ONLY`; normal public startup refuses while administration resumes the same descriptor, snapshots, and core.

## Qualification evidence

Under `conda activate torment` and SQLite `3.53.4`:

- `tests/test_b5_a5r0_admission_identity.py`: 2 passed.
- B5-A2/A3 fence and owner regressions: 24 passed.
- Existing multi-scope admission regressions, including normal fresh-root
  service startup: 3 passed.
- B5-A4R1/R2/R3 public startup regressions: 35 passed.

The R0 test builds equivalent legacy evidence through Fabric directly; the
existing admission suite separately retains its ordinary HTTP-service coverage.

## Remaining boundary

B5-A5 is **READY TO RESUME**, not performed. The separately authorized next slice is the offline cutover controller and its full crash/restart, public-service lifecycle, post-cutover read/write, abort, and no-rollback rehearsal. No real root was selected or moved.
