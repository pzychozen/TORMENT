# TORMENT database convergence — P1 staging writer-freeze requirement review v0.1

## Scope and terminology

Static repository review at 108510027fce2b85c5e064f330e86d1974351613 only.
No real root was contacted. No process census, WMIC, PowerShell, production SQLite
write, P1, P2+, service action, or source mutation occurred.

The following terminology is frozen for this review.

| Term | Meaning | Durable effect |
| --- | --- | --- |
| P1_BOOTSTRAP | First native staging-core creation: open_new_native_core_connection, create_schema, then native-only root-profile, scope, and membership prerequisites. | A new contained staging-core database and native metadata only. |
| P1_PREPARE_ROOT | OfflineCutoverController.prepare_root(request). | No durable write; builds and validates a candidate envelope from the existing core and source root. |
| P2_EXTERNAL_PENDING | record_root_admission_envelope followed by begin_cutover_pending. | Persists the immutable envelope record, then moves external selector authority to maintenance-only pending. |

P1_BOOTSTRAP is not prepare_root. A staging database can exist before
prepare_root is called, and that read-only preparation can be deferred until
immediately before P2. Read-only here does not mean source-free: the candidate
envelope reads the declared manifest and canonical source layout.

## Required ledger

P1_BOOTSTRAP_DEFINED = YES

P1_BOOTSTRAP_LEGACY_MUTATION = NO

P1_BOOTSTRAP_PUBLIC_AUTHORITY = NO

P1_BOOTSTRAP_SOURCE_COPY = NO

P1_PREPARE_ROOT_READ_ONLY = YES

ROOT_ADMISSION_ENVELOPE_FIRST_PERSISTED_AT = P2_EXTERNAL_PENDING

SELECTOR_FIRST_LEAVES_LEGACY_ACTIVE_AT = P2_EXTERNAL_PENDING

FULL_WRITER_FREEZE_FIRST_SEMANTICALLY_REQUIRED_AT = P2_EXTERNAL_PENDING when
the real-root-v2 entry uses build_real_root_v2_admission_envelope immediately
before persistence; current generic-controller enforcement is incomplete

P1_STALE_STATE_REVALIDATED_BEFORE_AUTHORITY = PARTIAL

P1_PRE_P2_STAGING_STATE_RECOVERABILITY = LIMITED

P6_POINT_OF_NO_RETURN = PRESERVED

RECOMMENDED_POLICY = BLOCKED

MACHINE_WIDE_COMMAND_LINE_CENSUS_REQUIRED_FOR_P1_BOOTSTRAP = NO

WINDOWS_PROCESS_COLLECTOR_WORK_REQUIRED_BEFORE_P1 = NO

P1_WRITER_FREEZE_REQUIREMENT_CAN_BE_NARROWED = NO

P2_PLUS_WRITER_FREEZE_REQUIREMENT_CHANGED = NO

REAL_ROOT_CONTACT = NONE

SQLITE_PRODUCTION_WRITE = NONE

P1_EXECUTED = NO

The narrowing verdict is an implementation-safety verdict. It does not say a
machine-wide census protects the inert database; the authority model supports a
split boundary conceptually. The present real-P2 entry wiring has not yet proven
a mandatory full-freshness gate at the point P2 starts.

## Exact P1 bootstrap write trace

The qualified direct-admission destination is one new contained file under
<data_root>/substrate/cores/<core>.db. RootOfflineCutoverRequest requires one
.db filename in that directory. The generic new-connection helper validates a
new .db destination but does not itself enforce containment; all conclusions
below apply to the qualified direct-admission use, not an arbitrary caller that
deliberately chooses another path.

| Operation | Durable target and records | Authority and source semantics |
| --- | --- | --- |
| open_new_native_core_connection | Creates the previously nonexistent contained SQLite file. SQLite can use adjacent journal sidecars while the qualified connection is open. | Opens no legacy source, initializes no schema, and selects no deployment authority. |
| create_schema | One transaction creates the declared native schema tables, indexes, and triggers, then inserts singleton core_metadata and deployment_metadata. | Values are core_role=STAGING, deployment_state=LEGACY_ACTIVE, and no referenced core. The schema has no copied legacy payload. |
| Root-profile prerequisite | Native identity, semantic, and idempotency namespace rows; NativeObjectService creates the ROOT_NATIVE_PROFILE_GENERATION object, immutable revision, operation/transition/effect records, and current-object pointer. | Native evidence/profile metadata. The qualification fixture uses authority category EVIDENCE; it is not a selector or public route. |
| Runtime and membership prerequisites | Native scope/namespace rows and staged scope objects required by the plan. RootScopeMembershipService uses NativeRelationshipService to write relationships, revisions/endpoints, operation/transition/effect, and idempotency records. | Typed native prerequisites bound to profile and runtime scope. They neither materialize a missing legacy scope nor route a public request. |

The bootstrap creates the complete empty native schema, including future
legacy-admission tables, but P1 inserts no legacy snapshots, artifacts,
admission records, aliases, normalized objects, representations, vectors,
motifs, or runtime payloads. The empty schema is capability, not copied source
state.

No reviewed P1 operation reaches workspaces, nodes.jsonl, embeddings, motif
state, character stores, SRG state, archive/deep stores, a legacy selector, or
any legacy source file. Its only qualified write surface is the new contained
native core. Data/substrate containment is a direct-admission request/launcher
constraint, not a property automatically imposed by the low-level helper.

Evidence: torment_service/substrate/connection.py lines 151-161; schema.py
lines 314-355; root_profile.py lines 63-124; root_scope_membership.py lines
211-229; objects.py lines 205-223; relationships.py lines 29-37.

## Lifecycle and public authority

After create_schema, the core is STAGING / LEGACY_ACTIVE, has no deployment
witness, and has never been active. With no selector, resolve_deployment_agreement
requires every controlled core be inert and returns LEGACY_PUBLIC. With an
existing LEGACY_ACTIVE selector, it repeats the inert-core requirement and
remains legacy public. Adding the database file never writes a selector marker,
selector row, witness, descriptor digest, profile digest, or selected core ID.

NativeProductionResourceOwner.from_native_agreement independently resolves a
fresh agreement and refuses anything other than NATIVE_AGREEMENT. The agreement
requires a selected core and matching witnesses. Root-v2 recovery also requires
an activation completion witness and an immutable persisted root-envelope
record. An inert P1 core has none of these facts, and restart cannot promote it.

The first selector departure is begin_cutover_pending: it examines a still
inert STAGING / LEGACY_ACTIVE core and changes only external selector state to
CUTOVER_PENDING. P5 later moves the core to STAGING / CUTOVER_PENDING. P6 alone
moves it to ACTIVE_CORE / NATIVE_ACTIVE; P7 then selects native. P6 remains the
point of no return, with no legacy fallback after native activation.

Evidence: deployment_selector.py lines 235-294, 468-481, and 637-647;
deployment_core_maintenance.py lines 159-208; production_native_owner.py lines
186-278 and 824-860.

## Envelope and P1_PREPARE_ROOT boundary

RootOfflineCutoverRequest requires a typed RootWriterFreezeWitness, but its
payload and recheck fields are optional. prepare_root calls _root_envelope,
verifies the core is inert, resolves a legacy-public agreement, and returns
evidence. It persists nothing.

_root_envelope opens the existing core and calls generic
build_root_admission_envelope. That builder validates writer witness and
optional payload/recheck, source manifest, canonical discovered census,
description/scope-plan parity, profile/membership closure, and runtime-scope
bindings. It returns an in-memory candidate only.

enter_root_external_pending builds the candidate again, checks inert state,
calls record_root_admission_envelope (the first durable record, in native
maintenance_events), then calls begin_cutover_pending (the first authority
transition). The record itself does not make the core public.

The real-root-v2 helper is stronger. build_real_root_v2_admission_envelope sets
require_writer_freeze_evidence_payload=True and rejects witness-only input
before source-root reads. The controller _root_envelope currently calls the
generic builder without that flag. The helper therefore defines the intended P2
semantic gate, but controller use does not make it mandatory for every caller.

Evidence: offline_cutover_controller.py lines 471-528 and 870-937;
deployment_core_maintenance.py lines 211-217; root_blocker5_binding.py lines
555-644 and 897-923.

## Writer-freeze contract matrix

| Phase | Actual required contract | Result |
| --- | --- | --- |
| A. Create inert database | New path and SQLite runtime qualification. No writer-witness argument. | Full freeze is not required by the API. |
| B. Populate native profile/membership/runtime prerequisites | Native structural and idempotency checks. No freeze-evidence argument. | Full freeze is not required by these persistence APIs. |
| C. Construct RootOfflineCutoverRequest | Typed RootWriterFreezeWitness. Payload/recheck optional. | Witness required; full payload proof is not. |
| D. P1_PREPARE_ROOT | Generic builder validates witness and, if supplied, payload plus fresh injected recheck. No write. | No universal payload requirement. |
| E. Persist RootAdmissionEnvelopeRecord | Real root-v2 helper requires payload and recheck. Generic controller builder permits witness-only. | Intended full P2 gate; not mechanically universal. |
| F. Enter CUTOVER_PENDING | Selector consumes the current envelope digest and requires inert-core facts. It does not collect observations. | Safe only when immediately-preceding P2 gate is strong and fresh. |
| G. P3 normalization | Controller rebuilds envelope before source copy under maintenance-only authority. Supplied payload is rechecked; generic witness-only remains possible. | Revalidation exists but is caller-evidence dependent. |
| H. P4 and P6 | P4 rebuilds envelope and verifies completion. P6 invokes P4 immediately before activate_core. Payload mode requires fresh injected recheck each time. | Source/closure and pre-P6 repeats exist; universal real-payload enforcement is still absent from controller wiring. |

RootWriterFreezeEvidencePayload contains writer-class observations, listener
and job observations, source-tree snapshots, and an external digest.
RootWriterFreezeRecheck validates supplied current observations and the current
workspace-tree snapshot against the frozen epoch. The verifier does not itself
start a process census or listener observer. It receives observations from its
caller and cannot make a stale packet fresh.

## Concurrent-writer race and staleness

A concurrent legacy writer cannot corrupt the new P1 schema through the
reviewed path: P1 writes a separate newly created database, not legacy files.
P1 does not copy legacy data, so it cannot copy a mixed source snapshot,
duplicate or lose a legacy write, create mixed public authority, or make later
normalization unsafe by copying anything in P1. It cannot route public
query/create/ingest to native because the selector remains legacy and the core
is unselected/inert.

A writer can still stale source facts used to plan runtime scopes, description,
or profile/membership prerequisites. The next envelope build checks manifest,
discovered-census parity, runtime-plan bindings, and native membership closure.
P4 and immediately pre-P6 repeat those checks and refuse mismatch instead of
promoting it.

That is partial, rather than complete, revalidation. The system does not
automatically rebuild a stale profile, scope plan, or membership set, and the
compatibility witness-only P2 controller route remains. A stale P1 core can be
refused before authority but lacks a complete qualified refresh/supersession
workflow.

## Disposability and recovery

safe_root_pending_abort validates an inert legacy state or returns a
never-active pending core to STAGING / LEGACY_ACTIVE. It deliberately does not
erase the core, envelope, or evidence. An unselected inert core can remain with
other inert controlled cores because the selector rejects only an unselected
core asserting cutover authority.

A fresh unique path can technically create a new core ID. That is not a
documented qualified recovery, rebuild, or supersession protocol for stale P1
prerequisites. No reviewed API lawfully deletes the old core, rewrites its
immutable prerequisites, or records a replacement relationship. The required
recoverability verdict is LIMITED, not QUALIFIED.

## Policy comparison

| Policy | Authority-model assessment | Verdict |
| --- | --- | --- |
| A — current strong form | Operationally conservative, but a machine-wide command-line census is not required to protect the isolated inert schema or P1 public authority. | Not architecturally necessary for P1 itself. |
| B — split boundary | Correct conceptual boundary: containment/non-collision P1, then full fresh source/writer gate directly before P2 and retained through P3/P4/P6. | Not qualified: real P2 gate is not mandatory in controller, observations are caller-injected, and stale-P1 rebuild/supersession is limited. |
| C — operator drain at P1 | Useful caution but cannot repair P2 mandatory-freshness gap or replace complete P2+ evidence. | Not sufficient to qualify a narrowing. |

The selected policy is BLOCKED. Do not weaken the operational P1 requirement in
this work order. This does not make machine-wide command-line collection a P1
bootstrap safety requirement; it is relevant only as an input to the required
full P2+ writer evidence. Therefore the current Windows inability to establish
arbitrary process command lines via PowerShell, Python-native collection, or
WMIC does not require more process-collector work before P1. It matters before
a real P2 gate that actually requires that evidence.

## Subsequent separately authorized implementation

No implementation was made. To qualify Policy B later, the smallest coherent
change set is:

1. Add a narrowly typed, contained P1_BOOTSTRAP workflow that records only
   new-core/profile/scope/membership prerequisites and expressly performs no
   source read, envelope persistence, or selector change.
2. Give the real root-v2 controller an explicit P2 method, or a prevalidated
   envelope input, that must come from build_real_root_v2_admission_envelope.
   Refuse payload-less or recheck-less input immediately before recording and
   pending selection. Preserve generic builder use only for declared
   synthetic/v1-compatible callers.
3. Define a qualified stale-P1 disposition: retain an inert core as evidence or
   supersede it with a new one, while rebuilding profile, scope plans,
   membership closure, and description before P2. Do not invent file deletion.
4. Add disposable tests proving real-controller witness-only P2 refusal, stale
   prerequisite/source refusal before selector transition, and legacy selector
   retention on every P1-only path.

Those changes must retain P3 maintenance, P4 verification, P5 core pending, P6
point of no return, P7 exact selector activation, no dual write, and the
prohibition on legacy rollback after P6.

## Test evidence

Existing disposable suites were run with an external temporary base and no
pytest cache:

    pytest -q -p no:cacheprovider --basetemp <external-disposable-base>
      tests/test_b5_a2_deployment_fence.py
      tests/test_b5_a3_production_native_resource_owner.py
      tests/test_post_i4_generalized_root_blocker5_binding.py
      tests/test_post_i4_root_v2_production_recovery.py
      tests/test_held_freeze_corrective_evidence_capture.py
      tests/test_root_writer_freeze_evidence.py

Result: 72 passed, 1 skipped.

They cover inert-controlled-core legacy resolution, selector ordering,
exact-native-owner refusal and root-v2 recovery evidence, missing/mismatched
envelope refusal at P4/pre-P6, pending abort, P2 tree-drift refusal, P4 and
pre-P6 freeze rechecks, and refusal of a witness-only real-root-v2 entry before
source-root reads. No review-specific test was needed and no runtime source
file changed.
