# TORMENT Memory Substrate — Post-I4 Root-v2 Production Recovery Bridge Qualification v0.1

## Scope and result

This qualification covers the bounded Post-I4 root-v2 immutable recovery-evidence
and version-aware production-owner bridge.  It is synthetic/offline only.

```
B1_ROOT_RECOVERY_EVIDENCE = PASS
B2_VERSION_AWARE_PRODUCTION_OWNER = PASS
V1_PRODUCTION_RECOVERY = PASS
I4G_PUBLIC_OWNER_ASSUMPTIONS_UNWIDENED = PASS
POST_P7_LEGACY_MEMORY_SOURCE_DEPENDENCY = NONE
```

The existing `NativeProductionResourceOwner` remains the sole production native
owner.  Durable activation-completion evidence selects either the unchanged v1
descriptor path or the v2 immutable-root-record adapter.  No second selector,
completion authority, deployment authority, or mutable recovery ledger was
introduced.

## B1: immutable root recovery evidence

`RootAdmissionEnvelope` now commits an ordered canonical tuple of
`MigrationRuntimeScopePlan` facts through `root_runtime_scope_plan_digest`; the
qualified profile must bind that exact digest.  A versioned
`RootAdmissionEnvelopeRecord` is persisted in the selected core's existing
immutable CUTOVER evidence stream before the P2 authority transition.  The
record carries the root description and census evidence, writer-freeze and
geometry evidence, full root-profile identity, membership closure, target lane,
profile payload, and recoverable canonical runtime plans.

The record recomputes the existing envelope digest rather than minting a second
authority.  It is read back after persistence and required again at P4 and
immediately before P6.  Records have an explicit contract and version; malformed,
noncanonical, conflicting, missing, or unsupported records refuse.

## B2: production recovery

The one production owner dispatches on the selected core's durable completion
witness.  The v2 adapter only loads selected-core evidence, validates it against
the selector/core/completion/profile/root-profile/membership/receipt/P7 chain,
and reconstructs per-workspace runtime views from the persisted scope-plan tuple.
It does not build an admission envelope, discover a root layout, verify a source
manifest, scan legacy workspaces, or execute a disposition.

Every admitted workspace must contain exactly one private scope and at least one
shared scope before a root-v2 owner is published.  Workspace views and query/write
contexts are keyed by workspace identity.  Root-v2 host configuration no longer
requires a descriptor path; supplied descriptor data cannot select its recovery
mode.  The diagnostic has a read-only root-v2 evidence path.

## Focused failure/refusal qualification

Synthetic tests prove fail-closed refusal with no legacy fallback or repair for:

- missing, noncanonical, conflicting, mismatched, or unsupported envelope evidence;
- unknown root-v2 completion version, completion/core and envelope drift, and
  root-profile or scope-plan-digest drift;
- missing/invalid runtime namespace evidence; missing, retired, or duplicate
  membership failure signals; and membership-closure drift;
- missing or completion/P7-mismatched disposition receipts;
- unsupported root public topology and pre-publication partial construction.

The valid restart test removes the synthetic legacy workspace layout before owner
construction and verifies repeated recovery from native evidence only.  No durable
writes occur in the recovery path.

## Exact test evidence

All commands used the `torment` Conda environment and disabled pytest's cache
provider.

```text
pytest -q -p no:cacheprovider --basetemp=_pytest_tmp_post_i4_root_v2_b1final tests\test_post_i4_generalized_root_blocker5_binding.py
7 passed in 2.27s

pytest -q -p no:cacheprovider --basetemp=_pytest_tmp_post_i4_root_v2_b2final tests\test_post_i4_root_v2_production_recovery.py
3 passed in 2.52s

pytest -q -p no:cacheprovider --basetemp=_pytest_tmp_post_i4_root_v2_matrix tests\test_post_i4_generalized_root_blocker5_binding.py tests\test_post_i4_root_v2_production_recovery.py
11 passed in 4.30s

python -m compileall -q <all changed production modules and focused tests>
pytest -q -p no:cacheprovider --basetemp=_pytest_tmp_post_i4_root_v2_fullfinal tests\test_post_i4_generalized_root_blocker5_binding.py tests\test_post_i4_root_v2_production_recovery.py tests\test_b5_a3_production_native_resource_owner.py tests\test_b5_a4r2_native_public_ingest_recovery.py
42 passed in 24.15s
```

No service entrypoint, REST/localhost endpoint, MCP server, provider, model,
embedding execution, real root, or disposable-root rehearsal was run.  The
historical full-root disposable rehearsal remains unrun in this phase; it may be
resumed separately after this bridge is accepted.
