# Real-root writer-freeze Class-B evidence adapter qualification v0.1

Status: `SYNTHETIC_QUALIFICATION`
Real writer freeze: `REAL_WRITER_FREEZE_NOT_EXECUTED`
Real root: `REAL_ROOT_NOT_CONTACTED`
Operator authorization: `FRESH_OPERATOR_AUTHORIZATION_REQUIRED`

## Administration history

```text
INITIAL_ADMINISTRATION = BLOCKED_PROCEDURAL_VIOLATION
INITIAL_BLOCK_REASON = BROADER_REGRESSION_STARTED_DISPOSABLE_LOCAL_SERVICE
INITIAL_SERVICE_VIOLATION_REAL_ROOT_EFFECT = NONE
IMPLEMENTATION_DISCARDED = NO

TOPOLOGY_FAILURE_CLASSIFICATION = UNRELATED
UNRELATED_TOPOLOGY_FAILURE =
  tests/test_post_i4_full_root_disposable_rehearsal_r1.py::
  test_r1_negative_root_public_topology_refuses_whole_root
TOPOLOGY_EVIDENCE =
  the assertion expects an exception for an additional private lane; the
  unchanged _require_root_v2_topology rule explicitly permits zero, one, or
  many private lanes when a workspace has an admitted shared lane.  The test
  request uses the legacy RootWriterFreezeWitness-only path, so the new payload
  and recheck path is not entered.  The isolated test reproduces the assertion
  mismatch without starting a service.

CORRECTED_ADMINISTRATION = PASS
FORMAL_TEST_RESULT = 59 passed, 1 skipped
SERVICE_STARTED_DURING_FORMAL_RERUN = NO
LOCALHOST_CONTACT_DURING_FORMAL_RERUN = NONE
MCP_STARTED_DURING_FORMAL_RERUN = NO
PROVIDER_CONTACT = NONE
MODEL_LOADING = NONE
REAL_ROOT_EFFECT = NONE
```

## Scope and authority

This implementation is a Class-B administrative evidence adapter.  A human
operator retains `STOP_AND_VERIFY_V1` enforcement authority.  The adapter
accepts typed, operator-supplied writer and listener observations, directly
reads only a nominated root's `workspaces/**` and bounded clone/repair job
status files, and validates the resulting proposition.  It does not start,
stop, restart, signal, or enumerate production processes; open a listener;
acquire a lock; create a core; change a selector; or write anywhere below the
observed root.

The new canonical immutable payload is
`TORMENT_ROOT_WRITER_FREEZE_EVIDENCE` version `1`.  It binds:

- root, freeze-operation, and operator identities;
- the exact five covered writer classes and only `STOPPED` / `ABSENT` results;
- a configured listener identity and an `ABSENT` result;
- bounded clone/repair job observation, for which only terminal historical
  statuses (`done`, `error`, `cancelled`, `abandoned`) are accepted;
- a deterministic `workspaces/**` snapshot at t0, t1, and t2;
- external-owner observation digest, admission-description contract label, and
  invalidation-rule version.

The payload's SHA-256 canonical digest must equal the existing
`RootWriterFreezeWitness.writer_evidence_digest`.  This preserves the existing
witness as the binding carrier and does not create a freeze or deployment
authority.

## Frozen source epoch

The snapshot walks only `workspaces/**` using direct file reads.  It records
canonical forward-slash relative paths, byte counts, and SHA-256 values, then
derives a stable tree digest, file count, and maximum file mtime.  Absolute
root paths are never fed to the tree digest, so byte-identical disposable
clones have the same tree digest while retaining distinct root identities.

Symbolic links and Windows reparse points are refused at the root, workspaces,
and traversed entries.  `jobs/**`, `lived_use/**`, and `substrate/**` are not
source-tree hash authority.  Jobs are checked separately only for active
clone/repair work.

The stability law is:

```text
t0.tree_digest == t1.tree_digest
t0.file_count  == t1.file_count
max(t0.max_mtime, t1.max_mtime) < t0
t2.tree_digest == t1.tree_digest
```

The administration procedure supplies `minimum_delta_seconds`; hashing never
sleeps or chooses a production wait interval.  t2 proves the read-only capture
did not change source files.

## Lifecycle binding and invalidation

Evidence-backed root requests require a fresh `RootWriterFreezeRecheck` at
every root-envelope construction.  That recheck validates fresh injected
writer/listener facts and the external-owner digest, while the adapter directly
rechecks the workspace snapshot and clone/repair statuses.  The existing root
controller rebuilds the envelope at P2, P4, and immediately before P6, so a
changed source tree, current non-terminal job, changed owner digest, invalid
fresh observation, or witness mismatch refuses rather than refreshing the
epoch.  The stable workspace digest and payload digest become fields of the
existing root-admission envelope digest; no second descriptor is created.

The epoch is historical/non-authorizing if the operator releases the freeze
before admission.  Writers may then resume, while selector and core authority
remain unchanged.  A later attempt requires new observations and new evidence;
the code does not repair or extend stale evidence.

The adversarial review's frozen-condition conclusion is used for the
open-handle statement: covered process death/absence plus listener absence,
no non-terminal job, and stable source epochs are the accepted operational
equivalent.  No separate unqualified open-handle probe is claimed or faked.

## Windows procedure boundary

The future human procedure runs under Windows CMD and gathers its host facts
outside this module.  It may activate the project environment with:

```cmd
call C:\Users\Notandi\miniconda3\condabin\conda.bat activate torment
```

Any platform-specific process or listener collector remains an injected narrow
observation seam.  It is not a process-management framework and is not present
in this qualification.

## Disposable qualification

Only pytest disposable roots were used.  The focused proof covers F1–F15:

- stable evidence and witness binding;
- t0/t1 and t2 mutation refusal;
- active listener, running writer, and non-terminal job refusal;
- file addition, deletion, rename, same-size byte change, and post-t0 mtime
  refusal;
- clone digest determinism; unsupported payload contract/version and
  witness/payload mismatch refusal;
- P2 stale-tree refusal, plus P4 and immediately-pre-P6 rechecks;
- terminal historical job acceptance and symlink/reparse refusal (the symbolic
  link test is skipped only if the local Windows test identity cannot create a
  symlink).

The predecessor root-v2 binding suite also passed unchanged.  No production
writer, listener, provider, model, BRAINVISION component, or real `data/` root
was contacted.

```text
WRITER_FREEZE_IMPLEMENTATION_CLASS = B
STOP_AND_VERIFY_FREEZE_MODEL = CONDITIONAL / SUFFICIENT UNDER FROZEN CONDITIONS
FREEZE_ESTABLISHMENT_REQUIRES_REAL_ROOT_WRITE = NO
ROOT_LOCK_CREATED = NO
RUNTIME_WRITER_INTEGRATION_CREATED = NO
NEW_DEPLOYMENT_AUTHORITY_CREATED = NO
NEW_FREEZE_AUTHORITY_CREATED = NO
```
