# TORMENT Memory Substrate — Post-I4 Full-Root Disposable Convergence Rehearsal R1

## Scope and outcome

Starting commit: `33176c2b1b342a81e9147082e906940e650a7460` (`origin/main` at administration start).

This record covers only fresh disposable roots created by
`tests/test_post_i4_full_root_disposable_rehearsal_r1.py`.  The ordinary
repository `data/` root was neither resolved nor opened by the test.  Every
fixture asserts that its disposable root is not that root and is not beneath
it.  The historical blocked R0 report remains unchanged.

`FULL_ROOT_DISPOSABLE_REHEARSAL_R1 = PASS`

The mandatory deterministic root-normalization arm passed.  The exact offline
service arm also passed using the locally complete `st` /
`BAAI/bge-small-en-v1.5` / `384` lane on CPU, with `HF_HUB_OFFLINE=1` and
`TRANSFORMERS_OFFLINE=1`.

## Primary disposable root evidence

The formal primary fixture was `r1-primary`, with data-root identity
`post-i4-r1:r1-primary`.  It contains two workspaces with deliberately
duplicate local qualifiers:

| Workspace | Private scope | Shared scope |
| --- | --- | --- |
| `north` | `same-agent` | `common-domain` |
| `south` | `same-agent` | `common-domain` |

The selected root core was `root-r1.db` with core ID
`8f157f3b-d002-44b3-9aac-1763ba612ddb`.  The final selector is generation 2,
`NATIVE_ACTIVE`, and binds:

- root admission envelope:
  `a9d914d3260c35ebcf40de1e985f740df01e0c6360d6133d5c7de75099a23a07`;
- runtime scope-plan digest:
  `b89bebb1e6edc627c45add3b56812579bae57b7013ce72c3222deb33f9b9860f`;
- qualified deployment-profile digest:
  `4877051627984e6fa05b4faa197e320a437f2fdf50cba54e6b0a46348dbb488f`;
- target representation identity:
  `st:BAAI/bge-small-en-v1.5:384:COMPAT_EMBEDDING`;
- root profile object/revision/ordinal:
  `947ca9a8-13d2-4c29-aa71-3b5e16e3dcf4` /
  `cd13deac-3ddf-431f-a19d-27cab553b9b3` / `1`;
- membership-closure digest:
  `767c0b63caf357fda38b8d1da5bedce1eb68ad3c52553e2c3cbb49aa32e4b03f`.

The persisted root envelope independently records the declared and discovered
census digests, respectively
`f4c98c721df407dc7610f91f275a116f333bf7e14a88d3c7eca689fab737941c` and
`07f995eafe707b84535e46a9bdba1378cfb10d513e61bcb3f8369fdf6f2e935f`, plus
the source-manifest digest
`cd86e119371eb70abe69d7c2a906acb576ef03ea000e87658b7fb58ea1e70681`.
The topology is exactly two workspaces, one materialized private scope and one
materialized shared scope per workspace, for four target-compatible scopes.

P2 installed the external pending selector fence.  P4 completion was verified
against the persisted envelope, scope plan, profile revision, membership
closure, writer freeze, census, and manifest.  P6 activated the core only
after that check; it is the durable point of no return.  The post-P6 frozen
disposition plan was executed through the disposable no-mutation adapter and
recorded receipt digest
`3cf40e922768c3549a35a179ad6e2b045d559202db9d1b6bf65cbc5c66d551bf`.
P7 rejected a deliberately wrong receipt intent and then bound that exact
receipt before making the selector native.

## Restart and service proof

The primary lifecycle deliberately creates new controllers at these windows:

1. after completion and before P6: `CORE_PENDING`, `ever_active=false`;
2. immediately after P6: `CORE_ACTIVE_EXTERNAL_PENDING`, maintenance-only,
   and safe abort refused;
3. after disposition and before P7: the same frozen receipt is recovered
   idempotently; and
4. after P7: `python -m torment_service` starts in `NATIVE` mode, then is
   stopped and restarted before a second native query.

No alternate server wrapper was used.  The service consumes the root-v2
selector/core agreement, completion witness, envelope, runtime scope plan,
profile, membership closure, and disposition receipt without an admission
descriptor path.

After the completed root was exercised, its disposable legacy `workspaces`
layout was renamed out of its canonical location.  A fresh production-service
start still reported native public mode, and a fresh
`NativeProductionResourceOwner` recovered the selected core.  This proves
post-P7 runtime authority has no dependency on that migration-source layout.

Qualified public behavior proved by the primary fixture:

- direct native public `get_workspace` and `create_agent` succeed only for
  pre-existing admitted identities in each workspace;
- `POST /agent/ingest` with an idempotency key and `POST /agent/query` succeed
  independently for `north/same-agent` and `south/same-agent`;
- a query in `south` does not return the private memory ingested in `north`;
- unadmitted private ingest is refused before effect;
- `POST /agent/trace` is refused;
- legacy-only HTTP workspace navigation and `/agent/create` are refused with
  the native fail-closed route boundary before legacy-memory effect; and
- native direct `create_agent` refuses an unadmitted identity.

## Negative arms and corrected administration

The R1 module includes fresh, separate disposable roots for: pre-active P5
abort, declared-census mismatch, pre-P6 manifest drift, and unsupported
two-private-scope public topology.  The topology arm refuses the whole root;
it does not permit partial startup.  The focused root-v2 recovery suite also
fails closed for missing/mismatched envelope and completion evidence, unknown
v2 evidence version, profile/scope-plan/root-profile/membership defects,
missing or retired membership, receipt mismatch, and partial topology.  No
case falls back to legacy or creates a second authority.

Three bounded implementation defects were found before the formal passing
root was created and corrected:

1. root P5 had no safe pre-active abort/resume path;
2. root-v2 native ingest storage did not forward its known workspace identity
   to recovery; and
3. root-v2 mutation-receipt lookup did not forward that workspace identity.

The corrections are deliberately limited to those paths.  The focused abort
test covers an idempotent pre-active abort, and the full service rehearsal
covers the two ingest propagation paths.  Earlier failed disposable roots
were not patched in place or used as the PASS evidence.

## Commands and results

All commands used Command Prompt with the `torment` Conda environment:

```text
call C:\Users\Notandi\miniconda3\condabin\conda.bat activate torment && pytest -q -p no:cacheprovider --basetemp=_pytest_tmp_post_i4_r1_primary_final tests\test_post_i4_full_root_disposable_rehearsal_r1.py::test_r1_full_root_disposable_lifecycle_service_restart_and_legacy_source_independence

call C:\Users\Notandi\miniconda3\condabin\conda.bat activate torment && pytest -q -p no:cacheprovider --basetemp=_pytest_tmp_post_i4_r1_full_restart_windows tests\test_post_i4_full_root_disposable_rehearsal_r1.py

call C:\Users\Notandi\miniconda3\condabin\conda.bat activate torment && pytest -q -p no:cacheprovider --basetemp=_pytest_tmp_post_i4_r1_regression tests\test_post_i4_root_v2_production_recovery.py tests\test_post_i4_generalized_root_blocker5_binding.py tests\test_post_i4_full_root_disposable_rehearsal_r1.py
```

The full R1 module passed (`3 passed`); the selected root-v2 regression suite
passes after the final changes (`15 passed`).  No disposable database is
committed.

## Final posture

```text
DISPOSABLE_ROOT_REAL_ROOT_SEPARATION = PASS
ROOT_TOPOLOGY = PASS
DISCOVERED_DECLARED_CENSUS = PASS
ROOT_ADMISSION_ENVELOPE_RECOVERY = PASS
ROOT_RUNTIME_SCOPE_PLAN_RECOVERY = PASS
ROOT_SCOPED_WRITER_FREEZE = PASS
PREACTIVE_ABORT = PASS
ROOT_NORMALIZATION = PASS
ROOT_COMPLETION_V2 = PASS
MANIFEST_RECHECK_PRE_P6 = PASS
P6_ACTIVATE_CORE = PASS
P6_POINT_OF_NO_RETURN = CONFIRMED
POST_P6_LEGACY_ABORT = REFUSED
DISPOSITION_EXECUTION = PASS
DISPOSITION_EXECUTION_RECEIPT = PASS
P7_RECEIPT_BINDING = PASS
P7_SELECTOR_NATIVE = PASS
POST_P7_NATIVE_AGREEMENT = PASS
ROOT_V2_PRODUCTION_SERVICE_START = PASS
POST_P7_LEGACY_SOURCE_DEPENDENCY = NONE
P6_TO_P7_RESTART = PASS
POST_P7_RESTART = PASS
PUBLIC_NATIVE_INGEST = PASS
PUBLIC_NATIVE_QUERY = PASS
CROSS_WORKSPACE_SCOPE_ISOLATION = PASS
UNADMITTED_SCOPE_REFUSAL = PASS
TRACE_REFUSAL = PASS
LEGACY_ONLY_PUBLIC_REFUSAL = PASS
ROOT_PUBLIC_TOPOLOGY_NEGATIVE_ARM = PASS
PARTIAL_ROOT_STARTUP = REFUSED
NATIVE_ACTIVE_LEGACY_FALLBACK = NONE
SECOND_CONTROLLER = NONE
SECOND_DEPLOYMENT_AUTHORITY = NONE
COMPRESSION = DISABLED
DEEP_MEMORY = DISABLED
NEW_SCOPE_CREATION = REFUSED
PRODUCTION_CODE_CHANGES = 3 bounded corrections
REAL_ROOT_CONTACT = NONE
REAL_ROOT_MUTATION = NONE
REAL_ROOT_ACTIVATION_READY = NO
REAL_PRODUCTION_ACTIVATION_AUTHORIZED = NO
BRAINVISION_OPENED = NO
SECOND_COGNITIVE_FUNCTION_INSPECTED = NO
TORMENT_MATHEMATICS_CHANGED = NO
```

This qualifies a root-wide production-shaped lifecycle only on a disposable
root.  It does not establish current real-root census, freeze, manifest, or
external-owner evidence.
