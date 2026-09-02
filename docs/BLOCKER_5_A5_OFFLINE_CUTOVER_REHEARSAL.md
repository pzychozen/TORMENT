# Blocker-5 B5-A5 — offline cutover controller and full rehearsal

## Verdict and production boundary

```text
B5_A5_OFFLINE_CUTOVER_CONTROLLER               = QUALIFIED
LEGACY_WRITER_DRAIN                            = QUALIFIED
P1_INERT_PREPARATION                           = QUALIFIED
FROZEN_LEGACY_SNAPSHOT                         = QUALIFIED
ADMISSION_UNDER_EXTERNAL_PENDING               = QUALIFIED
ADMISSION_RESUME_RECOVERY                      = QUALIFIED
PRE_ACTIVATION_VERIFICATION                    = PASS
CUTOVER_PENDING_PUBLIC_REFUSAL                 = PASS
CORE_PENDING_TRANSITION                        = PASS
CORE_ACTIVATION                                = PASS
EXTERNAL_SELECTOR_ACTIVATION                   = PASS
FINAL_NATIVE_AGREEMENT                         = PASS
POST_CUTOVER_NATIVE_PUBLIC_START               = PASS
MIGRATED_MEMORY_PUBLIC_READ                    = PASS
POST_CUTOVER_NATIVE_WRITE                      = PASS
POST_CUTOVER_RESTART_RECOVERY                  = PASS
PRE_ACTIVATION_ABORT                           = QUALIFIED
POST_ACTIVE_ROLLBACK                           = REFUSED
AUTOMATIC_POST_NATIVE_ROLLBACK_TO_LEGACY       = NO
POST_NATIVE_LEGACY_AUTHORITY                   = NONE
DUAL_WRITE_WINDOW                              = NONE
DUAL_READ_AUTHORITY_WINDOW                     = NONE
LEGACY_EVIDENCE_UNCHANGED_AFTER_NATIVE_USE     = PASS
REAL_PRODUCTION_CUTOVER_PERFORMED              = NO
KERNEL_FILES_CHANGED                           = 0
```

This is a complete rehearsal over pytest-created isolated roots. No real
production root, production selector, or user data was selected, moved,
activated, or modified. Compression and deep memory remain disabled for the
only qualified native profile.

## Administrative coordinator

`OfflineCutoverController` is deliberately stateless. It accepts a typed
`OfflineCutoverRequest` containing the pre-existing multi-scope admission
request, exact deployment profile, stable operator key, and an explicit
`OfflineWriterDrainWitness`. It never discovers or terminates processes.

It persists no new progress record and owns no public route or MCP tool.
Recovery derives only from existing evidence:

- selector-era and selector-ledger state;
- admission descriptor, immutable identity, completion witness, and snapshots;
- contained-core deployment and maintenance events; and
- the existing selector/core agreement resolver.

The controller's ordered operations are `prepare`, `enter_external_pending`,
`admit_under_external_fence`, `verify_completion`, `enter_core_pending`,
`activate_core`, and `activate_external_selector`. `current_stage` derives a
stage from durable facts rather than storing an administrative guess.

`safe_pending_abort` is restricted to a never-active core. It returns external
authority to `LEGACY_ACTIVE` only after the existing core abort evidence proves
that the core was not active. Once either selector or core has reached native
active state, it refuses; it is not a post-active rollback path.

## Rehearsed sequence and crash states

The full fixture starts a representative real legacy public service, creates
private `aria` plus shared `creative`, `engineering`, and `research` evidence,
with overlapping numeric EIDs, motifs/memberships, reinforcement/provenance,
bridge/external-owner evidence, and qualified vectors. The service is stopped
before P1 and the controller receives an explicit writer-drain attestation.

```text
P1  snapshots/manifests + inert STAGING/LEGACY_ACTIVE core
C0.5 legacy service restarts normally; prepared core has no public authority
P2  selector -> CUTOVER_PENDING; REST and MCP normal startup both refuse
P3  B2/B3A/B4A/B5 admission under the external maintenance fence
P4  completion witness, descriptor, staging readers, and cold lane readers verify
P5  core -> STAGING/CUTOVER_PENDING
P6  core -> ACTIVE_CORE/NATIVE_ACTIVE while selector remains pending
C5  restart state remains MAINTENANCE_ONLY; public start still refuses
P7  selector -> NATIVE_ACTIVE last, after exact active-core re-verification
P8  native REST/Spine/MCP reads, native keyed write, exact replay, and two restarts
```

The admission matrix stops and resumes after private B2, between private and
shared lanes, shared B3A, shared B4A, before B5, and after committed B5 with a
lost response. Every resumption uses the same operator/admission key and keeps
the same core UUID, admission identity, snapshots, manifests, and descriptor
lineage. A changed exact-profile request with that key refuses.

The rehearsal additionally proves C7 by discarding the first public write
response and retrying the same `Idempotency-Key` after restart. R2 returns the
identical completed result without another kernel cognition pass. C8 renames
the selected core in the isolated fixture; the resolver returns `REFUSED`
rather than guessing an authority or falling back to legacy.

## Native/legacy boundary

After P7, the test replaces every legacy `MemoryGraph` constructor, reader,
search, writer, and flush operation with a failure. REST `/agent/query`,
`/retrieve`, native keyed `/agent/ingest`, direct Spine query, MCP query, and
two complete native service lifecycles execute with zero legacy-memory calls.

The rehearsal hashes the entire legacy workspace before P1, verifies it again
after inert P1/C0.5 recovery, and again after all native reads, write, replay,
and restarts. Admission snapshot/manifests remain the immutable evidence
created at P1.

Qualification exposed one real leak: native `Fabric.ingest(...,
_prepare_only=True)` still advanced the legacy `RoleStore`, materializing or
rewriting `roles.json`. The repair is narrow:

- `RoleStore.load(create_if_missing=False)` returns the deterministic default
  role profile without writing it;
- selector-owned native query obtains role context read-only; and
- selector-owned native ingest skips role-profile updates while ordinary legacy
  ingest retains its original behavior.

This preserves shared Fabric cognition and its existing native R3 transport;
it does not add a new cognition algorithm, side-store owner, selector, or
fallback. The complete frozen-workspace digest now remains unchanged.

## Separate pending abort

A second isolated root stops after P5. It enters P1/P2, completes and verifies
admission, advances only to core pending, and safely aborts. Its core has never
been active, the selector returns to `LEGACY_ACTIVE`, legacy public startup is
again lawful, and the original legacy workspace digest is unchanged. Native
public authority never opens on that root.

## Evidence

Executed with `conda activate torment` and SQLite `3.53.4`:

```text
python -m pytest tests/test_b5_a5_offline_cutover_rehearsal.py -q
# 2 passed

python -m pytest tests/test_b5_a2_deployment_fence.py \
  tests/test_b5_a3_production_native_resource_owner.py -q
# 24 passed

python -m pytest tests/test_b5_a4r1_public_mutation_identity.py \
  tests/test_b5_a4r2_native_public_ingest_recovery.py \
  tests/test_b5_a4r3_public_backend_selection.py -q
# 35 passed

python -m pytest tests/test_substrate_existing_workspace_multi_scope_admission.py \
  tests/test_7g5e4e_native_query_read_model.py -q
# 8 passed

python -m pytest tests/test_7g5e4e_query_cognition_parity.py -q
# 10 passed
```

The next separately authorized work is B5-A6, the formal
production-shaped operator/diagnostics dress rehearsal. B5-A7 remains a later
formal Blocker-5 closure step. Neither is started by this change.
