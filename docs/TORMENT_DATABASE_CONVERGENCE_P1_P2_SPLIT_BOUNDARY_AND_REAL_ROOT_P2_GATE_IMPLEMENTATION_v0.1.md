# TORMENT Database Convergence: P1/P2 Split Boundary and Real-Root P2 Gate Implementation v0.1

## Scope and result

This qualification implements and tests the P1/P2 boundary using disposable
synthetic roots only.  It also closes an unrelated, stale root-v2 topology
test expectation.  It does not change production-owner topology code, direct
source grammar, writer-freeze semantics, database semantics, or later cutover
stages.

P1 is a source-free staging bootstrap.  It creates or classifies a contained
native core from explicit typed profile and runtime-scope facts.  P1 cannot
persist a root admission envelope, mutate the selector, enter cutover pending,
or create public native authority.

Real root-v2 P2 is now selected explicitly by `RootAdmissionMode.REAL_ROOT_V2`
and uses `build_real_root_v2_admission_envelope`.  The ordinary
`enter_root_external_pending` path is the real-root-v2 path.  The retained
generic v1/synthetic path is separately named
`enter_compat_root_external_pending` and requires
`RootAdmissionMode.SYNTHETIC_V1_COMPAT`.

## P1 bootstrap boundary

`real_root_staging_bootstrap.py` accepts an explicit core UUID, a contained
core path, typed root-profile facts, and typed runtime-scope membership facts.
It has no root-source, selector, writer-freeze, admission-envelope, or
normalization input.  A newly created core has the requested identity and
remains `STAGING` / `LEGACY_ACTIVE`, with no activation witness and no
historical native activation.

For an existing core path, exact inert facts are reusable.  A stale inert core
is retained and refused as stale; it is neither deleted nor superseded.  A
fresh request with a different path and identity creates a distinct core.
Multiple inert cores remain `LEGACY_PUBLIC`; only the fresh intended core can
subsequently be presented to the real P2 gate.

## P2 strong gate and ordering

The real P2 envelope builder is the single strong validation boundary.  It
refuses witness-only input, a payload without a typed recheck, and stale
rechecks before durable pending state is created.  For an accepted request,
the implementation retains the required order:

1. build the strong root-v2 envelope;
2. persist and reread the exact envelope record; and
3. begin selector `CUTOVER_PENDING`.

The regression coverage also proves that a later attempt to use the explicit
synthetic/v1 route cannot downgrade an already strong pending record, and that
a selector-transition failure leaves the durable envelope available for a
safe retry.

## Root-v2 topology correction

`production_native_owner._require_root_v2_topology` was not modified.  Its
existing law requires each root-v2 workspace to contain at least one admitted
shared lane and permits zero, one, or many private lanes.  The former
`test_r1_negative_root_public_topology_refuses_whole_root` expected an
exception solely because `north` had an extra private lane.  It was renamed
and corrected to assert successful owner recovery and the expected core
identity.

The true negative is retained in
`tests/test_post_i4g_r2_public_multi_topology.py::test_public_topology_gate_refuses_all_private_only_shapes`.
It supplies an otherwise structured workspace with no admitted shared lane
and verifies that production native-owner recovery refuses it.  Thus the
correction changes only an obsolete test assertion; multi-private support and
the shared-lane requirement remain covered.

## Disposable qualification evidence

All commands ran in the `torment` conda environment with external pytest base
temporary directories.  No real data root, production SQLite database,
service, WMIC process census, or production P-stage was contacted or run.

| Suite | Result |
| --- | --- |
| Corrected extra-private-lane rehearsal | 1 passed |
| `tests/test_post_i4g_r2_public_multi_topology.py` | 10 passed |
| P1/P2 focus: `test_real_root_staging_bootstrap.py`, `test_post_i4_generalized_root_blocker5_binding.py` | 18 passed |
| Requested broader disposable suite | 65 passed, 1 skipped |

The broader suite comprised `test_real_root_staging_bootstrap.py`,
`test_post_i4_generalized_root_blocker5_binding.py`,
`test_post_i4_full_root_disposable_rehearsal_r1.py`,
`test_post_i4_root_v2_production_recovery.py`,
`test_b5_a2_deployment_fence.py`,
`test_b5_a3_production_native_resource_owner.py`, and
`test_root_writer_freeze_evidence.py`.

## Qualification ledger

```text
P1_P2_SPLIT_BOUNDARY_IMPLEMENTED = YES
P1_BOOTSTRAP_WORKFLOW = QUALIFIED
P1_BOOTSTRAP_CONTAINED_NATIVE_ONLY = YES
P1_BOOTSTRAP_SOURCE_CONTACT = NONE
P1_BOOTSTRAP_LEGACY_MUTATION = NONE
P1_BOOTSTRAP_WRITER_FREEZE_REQUIRED = NO
P1_BOOTSTRAP_CORE_STATE = STAGING
P1_BOOTSTRAP_DEPLOYMENT_STATE = LEGACY_ACTIVE
P1_BOOTSTRAP_PUBLIC_AUTHORITY = NO
P1_BOOTSTRAP_ENVELOPE_PERSISTENCE = NONE
P1_BOOTSTRAP_SELECTOR_MUTATION = NONE

REAL_ROOT_V2_P2_STRONG_GATE = QUALIFIED
REAL_ROOT_V2_WITNESS_ONLY_P2 = REFUSED
REAL_ROOT_V2_PAYLOAD_WITHOUT_RECHECK_P2 = REFUSED
REAL_ROOT_V2_STALE_RECHECK_P2 = REFUSED
REAL_ROOT_V2_P2_BUILDER = build_real_root_v2_admission_envelope
SYNTHETIC_V1_COMPAT_GENERIC_BUILDER = PRESERVED_EXPLICITLY
P2_ENVELOPE_BEFORE_SELECTOR = PRESERVED
REAL_P2_DOWNGRADE_AFTER_STRONG_ENVELOPE = REFUSED

STALE_P1_EXACT_MATCH_REUSE = QUALIFIED
STALE_P1_SUPERSESSION = QUALIFIED
STALE_P1_DELETION = NONE
MULTIPLE_INERT_CORES_LEGACY_PUBLIC = PASS

ROOT_V2_STALE_TOPOLOGY_TEST_EXPECTATION = CORRECTED_TO_EXISTING_PRODUCTION_LAW
ROOT_V2_STALE_TOPOLOGY_TEST_EXPECTATION_CORRECTED = YES
UNRELATED_BASELINE_FAILURE = CLOSED
PRODUCTION_OWNER_TOPOLOGY_SEMANTICS_CHANGED = NO
PRODUCTION_TOPOLOGY_CODE_CHANGED = NO
ROOT_V2_TOPOLOGY_SEMANTICS_CHANGED = NO
TEST_EXPECTATION_CORRECTED = YES
MULTI_PRIVATE_LANE_SUPPORT = PRESERVED
SHARED_LANE_REQUIREMENT = PRESERVED

P3_SEMANTICS_CHANGED = NO
P4_SEMANTICS_CHANGED = NO
P5_SEMANTICS_CHANGED = NO
P6_POINT_OF_NO_RETURN = PRESERVED
P7_ORDERING_CHANGED = NO
NO_DUAL_WRITE = PRESERVED
NO_NATIVE_ACTIVE_LEGACY_FALLBACK = PRESERVED

WINDOWS_PROCESS_COLLECTOR_REQUIRED_BEFORE_P1 = NO
POLICY_B_SPLIT_BOUNDARY = QUALIFIED
REAL_ROOT_CONTACT = NONE
PRODUCTION_SQLITE_WRITE = NONE
```

## Non-actions

No real P1 occurred.  No real P2/P3/P4/P5/P6/P7 or Attempt 14 occurred.
