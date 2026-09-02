# Blocker-5 B5-A6 — formal production-shaped administration rehearsal

## Verdict and boundary

```text
B5_A6_PRODUCTION_SHAPED_ADMIN_REHEARSAL = PASS

DEPLOYMENT_DIAGNOSTIC = QUALIFIED
DIAGNOSTIC_SIDE_EFFECTS = NONE
DIAGNOSTIC_REDACTION = PASS

TWO_WINDOW_LEGACY_START = PASS
TWO_WINDOW_WRITER_DRAIN = PASS
TWO_WINDOW_PENDING_REFUSAL = PASS
TWO_WINDOW_ADMISSION = PASS
TWO_WINDOW_CORE_ACTIVATION = PASS
TWO_WINDOW_SELECTOR_ACTIVATION = PASS
TWO_WINDOW_NATIVE_START = PASS
TWO_WINDOW_NATIVE_RESTART = PASS

REST_MCP_DEPLOYMENT_AGREEMENT = PASS
INTERRUPTED_ADMIN_RECOVERY = PASS
SAFE_ABORT_OPERATOR_REHEARSAL = PASS

MANUAL_SQLITE_EDIT_REQUIRED = NO
DUAL_WRITE_WINDOW = NONE
DUAL_READ_AUTHORITY_WINDOW = NONE
PUBLIC_NATIVE_LEGACY_FALLBACK = NONE

REAL_PRODUCTION_CUTOVER_PERFORMED = NO
REAL_USER_MEMORY_ROOT_TOUCHED = NO
KERNEL_FILES_CHANGED = 0
KERNEL_MATHEMATICS_CHANGED = NO
KERNEL_GEOMETRY_CHANGED = NO
KERNEL_VECTORISATION_CHANGED = NO
KERNEL_RUNTIME_BEHAVIOR_CHANGED = NO
```

All A6 evidence uses disposable pytest roots. The formal root is
`_b5a6_pytest_tmp/test_b5_a6_formal_two_window_r0/formal-api-token-redacted-root`;
the separate never-active abort root is
`_b5a6_pytest_tmp/test_b5_a6_formal_two_window_r0/safe-abort-root`.
Both locations are test output only and are removed after qualification. No
production selector, native core, or user-memory root was named by the test.

## Read-only operator diagnostic

`torment_service.substrate.deployment_diagnostic.DeploymentDiagnostic` is the
single typed internal record. Its local operator projection is available via:

```cmd
conda activate torment
python -m torment_service.substrate.deployment_diagnostic --data-root <disposable-root>
```

The projection has this stable, redacted schema:

```text
schema / version
deployment_mode
selector_generation / selector_state
selected_core_id / core_id / core_role / core_deployment_state
sqlite_runtime_version / runtime_admissible
profile_qualified
admission_state / admission_identity_matches / completion_witness_valid
public_backend_mode
reason_code
```

`selected_core_id` is the selector's claimed UUID; `core_id` is the UUID read
from the contained core. This makes an identity disagreement visible without
printing a selector row or a core path.

The output excludes data-root and descriptor paths, selector contents,
descriptor payloads and digests, API keys, idempotency keys, request text, and
external-owner payloads. The redaction test deliberately uses path and
request-like token values and verifies none appear in the JSON projection.

Diagnostic observation calls the existing B5-A2 resolver, selector reader,
contained-core inspector, runtime qualifier, and descriptor validator. It has
no selector/core/admission mutation API, creates no `TormentFabric`, and opens
no writable selector or core connection. Repeated reads preserve the selector
generation/ledger, core metadata and maintenance events, descriptor, memory
tables, and complete root tree byte-for-byte.

The diagnostic reports `LEGACY`, `NATIVE`, or `REFUSED` as the public backend
that the existing public runtime could construct. It does not route a request
or choose a backend. A native result is possible only when the durable resolver
has already returned `NATIVE_AGREEMENT` and the existing host profile/descriptor
proof also validates. `MAINTENANCE_ONLY` and every refusal remain non-public.

For an actual native public process, the host supplies the existing proof facts
as an all-or-nothing pair: `TORMENT_DEPLOYMENT_PROFILE_JSON` (the exact typed
profile fields) and `TORMENT_ADMISSION_DESCRIPTOR_PATH`. They have no backend
mode field: missing, partial, malformed, or non-matching facts fail closed.
The durable selector still decides `LEGACY`, `NATIVE`, or `REFUSED`. REST,
MCP, and the diagnostic CLI consume the same pair.

## Two-window transcript

The formal test runs under the activated `torment` environment (SQLite
`3.53.4`). Window 1 always uses the production entry point,
`python -m torment_service`, with a specific disposable `TORMENT_DATA_DIR`.
Window 2 is the operator/client process: standard HTTP, the local diagnostic
CLI, the existing offline controller, and a separately constructed MCP runtime
against that same canonical root.

| Stage | Diagnostic before / action | Observed availability and result |
| --- | --- | --- |
| R0 | Fresh-root diagnostic | `LEGACY_PUBLIC`, `LEGACY`; no native authority. |
| R1 | Start service; create/use representative private plus three shared lanes; ordinary ingest/query | `/health` says `LEGACY`; legacy ingest/query pass. MCP resolves `LEGACY`. |
| R2 | Stop REST and MCP; record SHA-256 tree evidence of the legacy workspace | Writer drain completes before the controller receives its explicit drain witness. |
| R3 | `prepare` | Inert `STAGING/LEGACY_ACTIVE` core and incomplete descriptor; diagnostic remains `LEGACY_PUBLIC`. |
| R4 | `enter_external_pending`; attempt REST and MCP startup | `MAINTENANCE_ONLY`; both normal public startups refuse. |
| R5–R6 | Interrupt and resume existing admission; verify completion | Every observation remains maintenance-only. Completion becomes `ADMISSION_COMPLETE`, identity agreement and completion witness are true. |
| R7 | `enter_core_pending` | `STAGING/CUTOVER_PENDING`, still maintenance-only. |
| R8 | `activate_core`, then stop the administrative executor | `ACTIVE_CORE/NATIVE_ACTIVE` with selector pending; reason is `core-active-external-pending`; REST and MCP still refuse. |
| R9 | Fresh diagnostic CLI process, new stateless controller instance, `activate_external_selector` | `NATIVE_AGREEMENT`, `NATIVE`, qualified runtime/profile. |
| R10–R11 | Restart actual REST service; query migrated data; `/retrieve`; Spine query; keyed native REST ingest and exact retry | `/health` says `NATIVE`; read/query surfaces pass; replay has the exact first result. MCP resolves `NATIVE`. Frozen legacy workspace evidence is unchanged. |
| R12 | Stop and restart native service | `NATIVE_AGREEMENT` persists; migrated and new native memory are readable. |

The controller itself deliberately stores no process-local stage. The R8
interruption discards it, starts a fresh diagnostic process, reconstructs a
new controller from the same typed request, and completes R9 from durable
selector/core/descriptor evidence. No SQL shell, database editor, selector
edit, descriptor edit, or core-role edit is involved.

The B5-A4R3 focused transport suite remains the paired guard that replaces all
legacy `MemoryGraph` constructors/readers/writers with failures during native
REST, Spine, and MCP tests. It confirms that the successful production-shaped
native operations above have no legacy memory authority.

## Same-root MCP and refusal evidence

The rehearsal probes MCP in a separate process with `TORMENT_MCP_DATA_DIR`
equal to the REST root:

```text
pre-selector / legacy      REST = LEGACY, MCP = LEGACY
CUTOVER_PENDING            REST = REFUSED, MCP = REFUSED
NATIVE_ACTIVE agreement    REST = NATIVE, MCP = NATIVE
```

Diagnostic refusal fixtures cover a marker without selector, corrupt selector,
unavailable selected core, selected-core UUID mismatch, exact-profile mismatch,
synthetic ineligible SQLite witness, incomplete admission, invalid completion
witness, active core with external selector pending, and a synthetic read of a
native selector with a staging core. Every case is `REFUSED` or
`MAINTENANCE_ONLY`; none falls back to legacy. Fixture corruption is confined
to test construction and is not part of the operator transcript.

The second disposable root runs the existing controller through prepare,
external pending, completed admission, and core pending only. Its
never-active-core proof permits `safe_pending_abort`; the diagnostic returns
`LEGACY_PUBLIC`, and a real legacy service then starts. Native public authority
is never opened for that root.

## Evidence

Executed with `conda activate torment`:

```text
python -m pytest --basetemp=_b5a6_pytest_tmp \
  tests/test_b5_a6_production_shaped_administration_rehearsal.py -q
# 2 passed
```

The focused B5-A2/A3/A4R1/A4R2/A4R3/A5R0/A5 regression command passed
`63`; the query/MCP/trust/security command passed `159` with `2` intentional
skips; and the A6 formal command passed `2`. The temporary pytest base is
verified with `git clean -ndx` before exact cleanup; no user or production root
is a cleanup target.

B5-A6 closes the formal operator/diagnostic rehearsal only. B5-A7 is not
started by this change.
