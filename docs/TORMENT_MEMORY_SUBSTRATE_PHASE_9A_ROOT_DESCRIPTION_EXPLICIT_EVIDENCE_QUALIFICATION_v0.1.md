# TORMENT Memory Substrate Phase 9A — Root Description and Explicit Evidence Qualification v0.1

## Status

```text
PHASE_9A_ROOT_DESCRIPTION = PASS
EXPLICIT_SOURCE_MANIFEST = PASS
CENSUS_CONTRACT = PASS
OWNER_CONTAINMENT = PASS
RECOVERY_EVIDENCE_RECHECK = PASS

SUCCESSOR_OFFLINE_ADMINISTRATION = PASS
IMPLEMENTATION_CONTRACT = PASS
FOCUSED_9A_TESTS = PASS
VETTED_OFFLINE_REGRESSION = PASS
```

Phase 9A implements only the frozen generalized administrative/evidence
contract. It does not admit memory, create a native core or selector, select a
backend, or activate a public runtime.

## Historical administration record

The first Phase 9A qualification administration is retained as invalid.

```text
ATTEMPT_1 = ADMINISTRATION_INVALID
REAL_PRODUCTION_SERVICE_CONTACT_DURING_ATTEMPT_1 = YES
LIVE_REQUESTS = 2 x POST /agent/ingest
RESPONSES = HTTP 409, HTTP 409
ATTEMPT_1_REAL_ROOT_MUTATION = UNESTABLISHED
```

HTTP 409 is not interpreted as proof of zero effect. No follow-up production
root investigation was performed.

The successor administration first required no listener on port 8787, then
ran only statically vetted offline tests.

```text
SUCCESSOR_REAL_PRODUCTION_SERVICE_CONTACT = NO
SUCCESSOR_REAL_ROOT_CONTACT = NO
SUCCESSOR_REAL_MEMORY_MUTATION = NO
PHASE_9A_NETWORK_REQUIREMENT = NONE
```

## Regression containment

The invalid tests were:

- `test_real_multi_scope_admission_cold_recovery_vectors_and_resume`
- `test_admitted_e4c_research_lane_qualifies_authorized_proposal_storage`

Each is classified `REQUIRES_ISOLATED_TEMP_SERVICE` and is not eligible for
the Phase 9A successor regression. Their shared `_create_real_workspace`
helper configures a temporary `TORMENT_DATA_DIR` for a child service, but its
health and ingest calls are hard-coded to `http://127.0.0.1:8787`; it neither
uses `TORMENT_URL` nor proves the child owns that port. When port 8787 was
occupied, those calls reached the normal running service.

The successor inventory contained no network-capable test. Static inspection
found no localhost/8787, HTTP-client, service-startup, URL, or production-data
root construction in these selected files:

- `tests/test_substrate_root_admission_description.py`
- `tests/test_substrate_migration_inventory.py`
- `tests/test_substrate_migration_runtime_readiness.py`
- `tests/test_substrate_canonical_intent.py`
- `tests/test_substrate_ids.py`
- `tests/test_memory_graph_path_hardening.py`

Every storage fixture uses `tmp_path`, a temporary test connection, or a
temporary directory. The synthetic snapshot/inventory suite provides the
bounded snapshot coverage; no real root was opened to establish this.

```text
SUCCESSOR_REGRESSION_NETWORK_CAPABLE_TESTS = []
SUCCESSOR_REGRESSION_UNCONTAINED_EXTERNAL_SERVICE_TESTS = 0
```

The clean successor command completed with `53 passed in 2.48s`, including a
fresh rerun of all nine Phase 9A synthetic tests. `git diff --check` passed.

## Implemented contract

`RootScopeKey` defines only the non-colliding root-wide identities:

```text
PRIVATE = (workspace_id, PRIVATE, agent_id)
SHARED  = (workspace_id, SHARED, domain_id)
```

It validates structural components, requires exactly the applicable qualifier,
and serializes only for deterministic evidence ordering.

`RootNativeProductionAdmissionDescription` is an immutable future-admission
input. It binds a root identity, operator identity, canonical multi-workspace
plans, the frozen target lane (`st` / `BAAI/bge-small-en-v1.5` / `384`), typed
census, evidence-manifest digest, external-owner-observation digest, feature
posture, and writer-freeze state. It can express identity-only agents,
declared-but-unmaterialized domains, zero/one/multiple private or shared
materialized scopes, and motif-only empty shared scopes. It cannot certify
activation in Phase 9A.

`RootEvidenceManifest` names explicit owner-bounded present or absent sources
from a closed owner-class vocabulary. It binds canonical owner-relative
locator, role, scope identity where applicable, expected presence, and for
present files byte length plus SHA-256. Rechecks read only named locators and
refuse declared-source drift, required-source deletion, and creation of an
expected-absent source. Unrelated co-located files neither alter the digest nor
fail recheck.

Containment uses the existing `safe_join`/structural-component path-security
doctrine; no second containment system or recursive workspace fingerprint was
introduced. A declared unmaterialized domain may name only an explicitly
absent `UNMATERIALIZED_DECLARATION` source expectation. A materialized memory
scope requires present node evidence; absence cannot silently relabel it as
unmaterialized.

External owner observations remain evidence only. The implementation freezes:

```text
SEMANTIC_ADAPTER_OWNERSHIP != DURABLE_STORE_OWNERSHIP
CENSUS_AND_MANIFEST_REQUIRE_WRITER_FREEZE = YES
GEOMETRY_DERIVED_EXTERNAL_STATE_DISPOSITION = UNRESOLVED_PRE_ACTIVATION_GATE
```

## Boundary and convergence accounting

```text
NEW_PARALLEL_PUBLIC_RUNTIME = NO
NEW_DURABLE_SCOPE_REGISTRY = NO
FIRST_PROFILE_MUTATION = NO
RECURSIVE_WORKSPACE_FINGERPRINT = NO
MULTI_LANE_ACTIVE_AUTHORITY = NO

NEW_TRANSITIONAL_DUPLICATION =
    generalized root admission description and explicit owner-bounded
    evidence manifest; administrative only

EVENTUAL_REPLACEMENT =
    first-profile generalized-production evidence assumptions

FIRST_PROFILE_ADMISSION =
    RETAINED_AS_BOUNDED_IMPORT / QUALIFICATION SUPPORT

GENERALIZED_ROOT_DESCRIPTION =
    FUTURE PRODUCTION ADMISSION CONTRACT

LEGACY_RUNTIME_DELETION_AUTHORIZED = NO
```

```text
BRAINVISION_FILES_READ = 0
BRAINVISION_FILES_TOUCHED = 0
BRAINVISION_DATA_TOUCHED = 0
BRAINVISION_EVIDENCE_TOUCHED = 0
```

No real production root, memory model, external provider, selector, native
core, admission, cutover, or re-embedding operation was used by the successor
qualification.
