# TORMENT database convergence — direct admission path reconciliation

```text
STARTING_HEAD = c9bc355dc88c772ac018e477735c2b5f65dc7342
ANALYSIS_MODE = STATIC_REPOSITORY_RECONCILIATION_ONLY
REAL_ROOT_CONTACT = NONE
WRITER_CONTACT = NONE
PROVIDER_CONTACT = NONE
MODEL_LOADING = NONE
TESTS_RUN = 0
```

## Required verdicts

```text
CORRECTIVE_PACKET_PRODUCTION_DEPENDENCY = NO
DIRECT_ADMISSION_PREPARATION_EXPRESSIBLE = YES
SECOND_CONTROLLER_REQUIRED = NO
LEGACY_SOURCE_MUTATION_REQUIRED = NO
FRESH_WRITER_WITNESS_CAN_BE_CREATED_INLINE = YES

FIRST_REAL_MUTATION = P1_NATIVE_STAGING_CORE_BOOTSTRAP
FIRST_REAL_MUTATION_TARGET = data_root/substrate/cores/<native-staging-core>.db
CUTOVER_PENDING_INCLUDED = YES
PRE_P6_ABORTABILITY = PREPARED_OR_PENDING_MAY_RETURN_TO_STAGING_LEGACY_IF_NEVER_ACTIVE; RECORDS_ARE_NOT_ERASED
P6_REMAINS_POINT_OF_NO_RETURN = YES
```

`FIRST_REAL_MUTATION` is the answer from a purely frozen legacy root with no
native staging core. `open_new_native_core_connection(...)`, followed by
`create_schema(...)`, is the first durable bootstrap. It creates the inert
native core; it does not modify the legacy workspace. The root profile and
root-scope membership records are further P1 prerequisites in that same core.
`RootOfflineCutoverRequest` and `OfflineCutoverController.prepare_root()`
require that core, the current root profile, and the runtime/membership facts
to already exist; `prepare_root()` itself is read-only.

If those P1 prerequisites already exist, the first durable operation owned by
the root cutover controller is
`record_root_admission_envelope(...)`, called by
`OfflineCutoverController.enter_root_external_pending()`. It appends the
immutable envelope record to the inert core's `maintenance_events`. The same
method then establishes/initializes the selector only if absent and calls
`begin_cutover_pending(...)`, which changes the external selector from
`LEGACY_ACTIVE` to `CUTOVER_PENDING`.

## Production dependency boundary

The production root chain names no corrective-packet type or function:

```text
RootOfflineCutoverRequest
  -> OfflineCutoverController._root_envelope
  -> build_root_admission_envelope
  -> RootAdmissionEnvelope
  -> RootAdmissionEnvelopeRecord
  -> existing deployment selector / core maintenance / production native owner
```

`RootOfflineCutoverRequest` directly owns a
`RootNativeProductionAdmissionDescription`, `RootWriterFreezeWitness`, optional
typed writer payload/recheck, root profile, runtime scopes, a qualified
deployment profile, and a `RootNormalizationRequest` bound to the same
description. `_root_envelope()` passes those direct values to
`build_root_admission_envelope()`.

`RootAdmissionEnvelope` validates the discovered-versus-declared census,
explicit source manifest, writer binding/recheck when supplied, resolved
geometry plan, qualified profile, root profile, runtime scope plans, and
membership closure. `RootAdmissionEnvelopeRecord` persists an exact subordinate
copy. `NativeProductionResourceOwner._recover_root_v2_workspace_runtime()`
then reconstructs active runtime scopes solely from that persisted record plus
selector/core/completion authority; it does not load a corrective packet.

Repository-wide static references to `CorrectiveFreezePacket` outside tests
are confined to `corrective_freeze_packet.py` and
`real_root_typed_evidence.py`. The controller, root binding, deployment
selector, core maintenance, root normalizer, root membership, profile reader,
and production owner have no such dependency.

## Direct in-memory preparation sequence

The existing direct seam is sufficient after a future authorized read-only
preparation builds the existing typed inputs:

1. Perform the fresh writer census/listener/jobs observations and call
   `capture_root_writer_freeze_evidence(...)`. Its `during_capture` callback
   runs after stable t0/t1; it can construct source facts then, and its owner
   digest supplier binds the same in-memory description before t2. The function
   returns `CapturedRootWriterFreezeEvidence`, containing the typed payload and
   `RootWriterFreezeWitness`; it serializes no corrective packet.

2. Construct `RootNativeProductionAdmissionDescription` from fresh canonical
   source facts, then the existing `RootGeometryDispositionPlan`, runtime scope
   plans/scopes, qualified profile, root profile, and membership closure. Supply
   a fresh `RootWriterFreezeRecheck` with the payload and witness.

3. Construct `RootOfflineCutoverRequest` with those values. Its existing
   controller path is `prepare_root()` (P1 read-only) then
   `enter_root_external_pending()` (P2 envelope persistence and pending
   selector), followed by existing P3 through P7 methods.

4. For a real root-v2 caller, `build_real_root_v2_admission_envelope(...)`
   already requires the payload-bound writer evidence. The generic builder also
   verifies it whenever the payload and recheck are supplied. No second
   admission or cutover controller is needed.

The one narrow future seam is a direct, read-only source-to-description
preparation adapter that returns the already-existing description, discovered
census, source manifest facts, and geometry plan without returning or
serializing a `CorrectiveFreezeTypedEvidence` packet object. Today the only
source extractor that constructs those objects is
`RealRootTypedEvidenceAdapter.capture_typed_evidence()` in the closed
corrective support lane. That is a construction boundary, not a production
admission dependency and not a reason to change the historical packet tooling.

## Source and empty-shared law

The immutable description already encodes the practical distinction:

```text
nodes.jsonl absent => canonical memory count = 0
EMPTY_SHARED_WITH_MOTIF => zero memory objects and zero representation migration requests
EMPTY_SHARED_WITH_MOTIF => present motif evidence may still close
```

`RootNativeProductionAdmissionDescription._validate_manifest_against_plans()`
requires `EMPTY_GRAPH` absence evidence for nodes and present motif evidence
for `EMPTY_SHARED_WITH_MOTIF`. Storage or retained residue is consequently not
promoted to memory. Future direct preflight must continue to refuse a genuinely
unknown canonical durable path; it must not redefine `shared/` as byte-empty.

The source-authority split remains unchanged: canonical nodes are memory
authority; `workspace_meta.json` owns representation identity; embedding
storage is derived/storage evidence; Character and RoleStore remain external;
SRG markers remain retained; archive/deep remain retained/disabled initially;
motifs retain their existing authority; orphan vectors without canonical nodes
are not memories.

## Durable transition and abort boundary

```text
DIRECT_PREPARATION  read-only, in-memory typed facts and writer evidence
P1                  create inert STAGING/LEGACY_ACTIVE core and prerequisite profile/membership facts
P2                  persist RootAdmissionEnvelopeRecord; selector -> CUTOVER_PENDING
P3                  NativeRootWideNormalizationService under maintenance-only authority
P4                  verify_root_completion; no selector/core activation
P5                  core -> STAGING/CUTOVER_PENDING
P6                  core -> ACTIVE_CORE/NATIVE_ACTIVE (point of no return)
P7                  selector -> NATIVE_ACTIVE last
```

`safe_root_pending_abort()` is the existing pre-P6 recovery path. It requires
a never-active core, restores a P5 core through `abort_cutover_pending()` when
needed, then restores the selector through `abort_selector_pending()` to
`LEGACY_ACTIVE`. It does not erase the inert core, envelope record, or any
other durable evidence. There is intentionally no native-active-to-legacy
transition after P6.

## Next operator authorization boundary

```text
NEXT_OPERATOR_AUTHORIZATION_BOUNDARY = ONE_FUTURE_DIRECT_ADMISSION_PREPARATION_RUN
```

That authorization must separately name: the permitted fresh read-only source
contact and writer observations; the direct source-to-description adapter
boundary above; and, before any mutation, the P1 staging-core bootstrap target
and operator key. This reconciliation authorizes none of those operations and
does not authorize a packet retry, a new packet version, source repair, or any
legacy-source modification.
