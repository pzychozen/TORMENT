# TORMENT direct source-to-admission preparation qualification

```text
DIRECT_SOURCE_TO_ADMISSION_SEAM = QUALIFIED
CORRECTIVE_PACKET_DEPENDENCY = NO
SOURCE_READER_DUPLICATION = NO
DIRECT_WRITER_FREEZE_CALLBACK_INTEGRATION = PASS
ROOT_ADMISSION_ENVELOPE_INTEGRATION = PASS

FIRST_REAL_MUTATION_REMAINS = P1_NATIVE_STAGING_CORE_BOOTSTRAP
FIRST_REAL_MUTATION_TARGET = data_root/substrate/cores/<native-staging-core>.db
LEGACY_SOURCE_MUTATION_REQUIRED = NO
PACKET_VERSION_CHANGED = NO
NEW_HASH_LAW = NO
NEW_BYTE_IDENTICAL_LAW = NO
```

## Implemented seam

`RealRootTypedEvidenceAdapter.prepare_direct_admission_source()` now returns
the immutable `DirectAdmissionSourcePreparation` result directly in memory:

```text
RootNativeProductionAdmissionDescription
RootDiscoveredCensus
RootGeometryDispositionPlan
RootSourceScopePlan tuple
UNKNOWN_IDENTITY evidence
EMPTY_PRIVATE evidence
DECLARED_EMPTY_SHARED evidence
```

`_prepare_source()` is the sole source-reading implementation. The historical
`capture_typed_evidence()` method is retained only as a compatibility projection
for corrective support tooling; it calls the same reader and produces no second
scanner. The direct method creates no packet, creates no serialization target,
and does not reload source facts.

The direct empty-shared branch recognizes only established retained/storage
leaves (`embeddings`, `memory_events.jsonl`, `logs`, and `trajectories`). It
validates storage structure as derivation evidence, does not add it as canonical
memory evidence, and still refuses an unknown direct child. Thus an
`EMPTY_SHARED_WITH_MOTIF` scope has absent `nodes.jsonl`, zero canonical memory
objects, `NO_VECTOR`, and lawful motif closure even when known residue remains.

Representation identity remains read from `workspace_meta.json`; storage
manifests only detect a contradiction and never infer provider/model identity.
The qualified target, legacy hash, and three permitted metadata-less scopes
retain their existing dispositions. External Character, RoleStore, seeds,
SRG-retained state, archive/deep posture, motifs, and alternate `lived_use`
presence-only handling are unchanged.

## Inline writer and envelope integration

The qualification invokes the direct method from
`capture_root_writer_freeze_evidence(..., during_capture=...)`. The owner digest
supplier binds the same in-memory description before t2, yielding the existing
`CapturedRootWriterFreezeEvidence` payload and `RootWriterFreezeWitness`.

On a disposable root, that output plus a fresh `RootWriterFreezeRecheck` feeds
`build_real_root_v2_admission_envelope(...)` successfully. The test uses the
existing root profile and qualified profile contracts; it creates no controller,
selector, cutover state, normalization, P6 activation, packet, provider, or
workspace runtime.

## Qualification

```text
tests/test_real_root_typed_evidence_adapter.py
  25 passed, 1 skipped

tests/test_root_writer_freeze_evidence.py
tests/test_substrate_root_admission_description.py
tests/test_post_i4_generalized_root_blocker5_binding.py
tests/test_post_i4_root_v2_production_recovery.py
  40 passed, 1 skipped

TOTAL_FINAL_QUALIFICATION = 65 passed, 2 skipped
```

The default Windows pytest temp root was inaccessible, so each focused run used
a fresh workspace-local `--basetemp`; the only resulting warning was pytest's
unwritable cache path. No test failure was attributable to the seam.

```text
CORRECTIVE_PACKET_USED = NO
PACKET_SERIALIZATION_USED = NO
SECOND_CONTROLLER_CREATED = NO
LEGACY_SOURCE_WRITE = NONE
WORKSPACE_RUNTIME_OPEN = NONE
EMBEDDING_STORE_OPEN = NONE
PROVIDER_CONTACT = NONE
MODEL_LOADING = NONE
CHARACTER_SEMANTICS_CHANGED = NO
SRG_SEMANTICS_CHANGED = NO
CORE_MEMORY_SEMANTICS_CHANGED = NO

REAL_ROOT_CONTACT = NONE
WRITER_CONTACT = NONE
BRAINVISION_OPENED = NO
SECOND_COGNITIVE_FUNCTION_INSPECTED = NO
```

## Terminal boundary

```text
NEXT_OPERATOR_AUTHORIZATION_BOUNDARY =
DIRECT_REAL_ADMISSION_PREPARATION_AND_P1_STAGING_BOOTSTRAP
```

This qualification authorizes neither real source contact nor the first real
write. P1 remains the explicit creation of inert native staging state at the
named core path; it must not modify the legacy workspace. No `CUTOVER_PENDING`,
normalization, P6, P7, service restart, packet retry, or source repair occurred.
