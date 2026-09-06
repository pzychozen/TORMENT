# TORMENT Real-Root P1 Staging Bootstrap Attempt 1 Result v0.1

## Result

The real-root P1 prerequisite materialization completed under Attempt 2, and
the first real P1 staging bootstrap completed under its separate P1 operation
identity.  The operation stopped after P1 review; no P2 or later cutover work
was performed.

```text
MATERIALIZATION_ATTEMPT = 2
MATERIALIZATION_OPERATION_ID = real-root-p1-prerequisite-materialization-attempt-2-20260906
P1_OPERATION_ID = real-root-p1-staging-bootstrap-attempt-1-20260906
STARTING_HEAD = 6445c15fc7ce7a68f0f8b770dc72c80c849292b4

REAL_ROOT_P1_DECLARED_DOMAIN_TOPOLOGY_READ = PASS
REAL_ROOT_P1_PREREQUISITE_MATERIALIZATION_ATTEMPT_2 = PASS
DECLARED_DOMAIN_SOURCE = domains.json
WORKSPACES = 51
PRIVATE_RUNTIME_SCOPES = 76
MATERIALIZED_SHARED = 48
DECLARED_EMPTY_SHARED = 30
TOTAL_SHARED_RUNTIME_SCOPES = 78
TOTAL_RUNTIME_SCOPES = 154
P1_NATIVE_IDENTITY_PLAN = FROZEN

REAL_ROOT_P1_STAGING_BOOTSTRAP_ATTEMPT_1 = PASS
REAL_NATIVE_STAGING_CORE_CREATED = YES
REAL_NATIVE_STAGING_CORE_PATH = data/substrate/cores/root-native-staging-0e9cb4b7-cf57-49fa-b60a-0e5a25f9d288.db
REAL_NATIVE_STAGING_CORE_ID = 0e9cb4b7-cf57-49fa-b60a-0e5a25f9d288
P1_RESULT_DISPOSITION = CREATED

CORE_ROLE = STAGING
CORE_DEPLOYMENT_STATE = LEGACY_ACTIVE
CORE_EVER_ACTIVE = NO
DEPLOYMENT_WITNESS = NONE
ROOT_PROFILE_OBJECT_ID = 67bd26ba-ca81-426f-8f7d-7a8996776a3c
ROOT_PROFILE_GENERATION = 1
ROOT_PROFILE_SEMANTIC_SCOPE_ID = efeffb93-2e35-4096-8436-e00f8c0b93ec
ROOT_MEMBERSHIP_COUNT = 154

P1_BOOTSTRAP_POST_PLAN_SOURCE_CONTACT = NONE
P1_BOOTSTRAP_LEGACY_MUTATION = NONE
ROOT_ADMISSION_ENVELOPE_PERSISTED = NO
CUTOVER_PENDING = NO
NORMALIZATION_EXECUTED = NO
PUBLIC_DEPLOYMENT = LEGACY_PUBLIC
NATIVE_PRODUCTION_OWNER_PUBLIC_AUTHORITY = NO

P2_EXECUTED = NO
P3_EXECUTED = NO
P4_EXECUTED = NO
P5_EXECUTED = NO
P6_EXECUTED = NO
P7_EXECUTED = NO
STOPPED_FOR_P1_REVIEW = YES
```

## Boundary observations

Attempt 1 materialization was previously refused before plan creation and
before any native state because it treated only physically present domain
directories as declarations.  That closed attempt was not modified or reused.

Attempt 2 used the existing `Workspace.domains` / `domains.json` declaration
semantics.  It read only the allowed declaration files and directory topology,
then froze an external machine-readable plan before creating the core.  After
that freeze, P1 and its verification consumed the plan and the newly created
native core only; they did not read `workspaces` again or mutate legacy data.

The external plan, administration event log, runner, and native SQLite core
are runtime/administration state and are intentionally not Git evidence.
