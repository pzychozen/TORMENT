# TORMENT DATABASE CONVERGENCE

## P2/P3 Recovery Durability Repair Qualification v0.1

Starting head: `2b3cbcc29398a0e4413d0165f676f1c6f1ce5ed5`

P2_P3_RECOVERY_DURABILITY_DEFECT = CONFIRMED

The prior successful real P2 record retained the writer-freeze witness and
payload digest, but not the serialised `RootWriterFreezeEvidencePayload`.
That payload cannot be derived from a digest, so P3 recovery from that exact
historical P2 remains blocked pending separately authorised real-root action.

ROOT_ENVELOPE_V1_COMPATIBILITY = PRESERVED

`RootAdmissionEnvelopeRecord` remains version 1 and decodes unchanged. A new
subordinate `RootWriterFreezeEvidenceRecord` binds one existing envelope digest
to the exact versioned writer-freeze payload, its witness payload, payload
digest, and frozen workspace tree digest. Construction and decoding require
typed payload decoding, witness binding, payload/tree equality, envelope
cross-binding, and external-owner agreement.

FULL_WRITER_FREEZE_PAYLOAD_DURABILITY = QUALIFIED

REAL_ROOT_V2_PAYLOAD_RECORD_REQUIRED_BEFORE_SELECTOR_PENDING = YES

For `REAL_ROOT_V2`, the qualified order is now:

1. Build the strong envelope and persist/reread its existing v1 record.
2. Persist/reread the subordinate exact writer-freeze evidence record.
3. Only then initialize/advance the selector to `CUTOVER_PENDING`.

An injected evidence-record persistence failure leaves the selector in the
pre-selector legacy-public state; no pending authority is created.

P2_EXTERNAL_PENDING_INERT_CORE_ABORT = QUALIFIED

The new P2-only recovery transition requires an exact pending selector,
generation, descriptor digest, profile, selected core, and self-validating
persisted envelope. It independently requires the selected core to remain
exactly `STAGING / LEGACY_ACTIVE / no witness / never active`, then clears only
selector authority to `LEGACY_ACTIVE`. The core and durable evidence remain.

P5_ABORT_PATH_CHANGED = NO

POST_P6_ROLLBACK_CHANGED = NO

SUCCESSOR_P2_AFTER_ABORT = QUALIFIED

MULTIPLE_HISTORICAL_ENVELOPES = SUPPORTED_BY_EXACT_DIGEST_SELECTION

The disposable successor cycle retained envelope/evidence A after inert abort,
then persisted distinct envelope/evidence B and bound the pending selector only
to B. Evidence A refused cross-binding to envelope B.

P3_PROCESS_LOSS_RECOVERY = QUALIFIED

The successor fixture recovered the exact payload and witness from the durable
record, constructed a fresh `RootWriterFreezeRecheck`, and rebuilt the strong
envelope with a digest exactly equal to the selector descriptor.

Focused disposable-root regression results:

- `tests/test_post_i4_generalized_root_blocker5_binding.py`: 27 passed
- `tests/test_root_writer_freeze_evidence.py`, `tests/test_post_i4_root_v2_production_recovery.py`, `tests/test_b5_a2_deployment_fence.py`, `tests/test_real_root_staging_bootstrap.py`: 38 passed, 1 skipped
- `tests/test_post_i4_full_root_disposable_rehearsal_r1.py`: 3 passed
- `tests/test_real_root_typed_evidence_adapter.py`: 51 passed, 5 skipped

REAL_ROOT_CONTACT = NONE

REAL_ROOT_WRITE = NONE

CURRENT_REAL_P2_ABORT_EXECUTED = NO

P3_EXECUTED = NO

P4_EXECUTED = NO

P5_EXECUTED = NO

P6_EXECUTED = NO

P7_EXECUTED = NO

The current real root remains `CUTOVER_PENDING` / `MAINTENANCE_ONLY` with an
inert staging core. This qualification does not retry P2, execute the new abort,
or authorize or execute P3.
