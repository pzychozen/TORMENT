# Blocker-5 B5-A2 — Durable Deployment Fence and Selector

## Status

`B5-A2` is complete as a qualification-only deployment-administration foundation. It adds no REST, MCP, `TormentFabric`, public ingest, public query, dual-read, dual-write, or public native-routing behavior.

```text
DURABLE_SELECTOR_IMPLEMENTED = YES
WRITE_ONCE_SELECTOR_ERA_IMPLEMENTED = YES
CORE_PENDING_AND_ACTIVE_MAINTENANCE_IMPLEMENTED = YES
PURE_AGREEMENT_RESOLVER_IMPLEMENTED = YES
NATIVE_AGREEMENT_IS_PUBLIC_ACTIVATION = NO
PUBLIC_INGEST_BACKEND = LEGACY
PUBLIC_QUERY_BACKEND = LEGACY
NATIVE_ACTIVE_RUNTIME = NO
```

This record is the B5-A2 implementation/qualification record. The prior [B5-A1 environment convergence record](BLOCKER_5_A1_PRODUCTION_ENVIRONMENT_CONVERGENCE.md) remains the authoritative proof of the ordinary `torment` environment's exact SQLite runtime.

## Durable authority boundary

The selector has a deliberately small, external ownership boundary:

```text
<data_root>/substrate/deployment/selector-era-v1.json
<data_root>/substrate/deployment/selector.sqlite
<data_root>/substrate/cores/<contained-core-filename>.db
```

No request, workspace, agent, MCP argument, URL component, or ambient public runtime setting supplies these paths. Selected core names are single contained `.db` filenames; root/core symlinks and escapes are refused.

The era document is canonical and static:

```text
contract = TORMENT_B5_A2_SELECTOR_ERA
schema_version = 1
selector_era = selector-era-v1
authority = NONE
```

It records no mutable deployment decision. It is atomically created once and only accepts its exact canonical contents on recovery. A selector without its marker, a marker without a selector, a malformed marker, a malformed selector, or an incompatible selector schema is refused rather than treated as legacy.

`selector.sqlite` is a dedicated, same-thread SQLite administration database, not an ORM model and not a semantic-memory carrier. It stores one current selector snapshot plus an immutable ledger. Each ledger record carries its previous and new generation/state/core/descriptor/profile/witness facts, operation key, canonical intent, reason kind, and timestamp. The state singleton must agree with the complete contiguous ledger.

Generation zero is the durable `LEGACY_ACTIVE` initialization record. Every later selector transition requires the exact expected predecessor generation and state and advances generation by exactly one. Retrying an identical operation key and canonical intent returns its committed receipt without a new generation; reusing the key with a changed intent is refused.

## State fence and ordering

The implementation reuses the existing native-core vocabulary without adding new core state tables or enums:

| External selector | Selected core | Resolver disposition |
|---|---|---|
| absent marker + absent selector + no claim | none or inert `STAGING/LEGACY_ACTIVE` | `LEGACY_PUBLIC` |
| `LEGACY_ACTIVE` | none or inert `STAGING/LEGACY_ACTIVE` | `LEGACY_PUBLIC` |
| `CUTOVER_PENDING` | untouched staging, pending staging, or active core | `MAINTENANCE_ONLY` |
| `NATIVE_ACTIVE` | exact `ACTIVE_CORE/NATIVE_ACTIVE` core and exact qualified witness/profile/runtime | `NATIVE_AGREEMENT` |
| any mismatch, corruption, missing core, unselected claim, wrong profile/runtime | any | `REFUSED` |

`NATIVE_AGREEMENT` is a startup fact only. It deliberately does not select a public backend.

The only durable forward sequence is:

```text
external LEGACY_ACTIVE -> CUTOVER_PENDING
core     STAGING/LEGACY_ACTIVE -> STAGING/CUTOVER_PENDING
core     STAGING/CUTOVER_PENDING -> ACTIVE_CORE/NATIVE_ACTIVE
external CUTOVER_PENDING -> NATIVE_ACTIVE
```

Core transitions use an existing qualified maintenance connection and one transaction to update `core_metadata`, `deployment_metadata`, and an immutable `maintenance_events` record of kind `CUTOVER`. The B5-A2 event binds the core UUID, pre/post witness, selector generation/witness, descriptor/profile digests, operation key, canonical intent, and timestamp. Existing staging runtime binding rejects `ACTIVE_CORE`, so this work does not open the existing staging writer/binding path to an activated core.

The sole reversal is the safe pending abort:

```text
core     STAGING/CUTOVER_PENDING -> STAGING/LEGACY_ACTIVE
external CUTOVER_PENDING -> LEGACY_ACTIVE
```

It requires a matching `ABORT_CUTOVER_PENDING` receipt and proof that the core has never reached `ACTIVE_CORE/NATIVE_ACTIVE`. No `NATIVE_ACTIVE -> LEGACY_ACTIVE` external transition exists.

## Profile and resolver qualification

The effective-profile witness is a canonical digest of the actual effective facts, not environment-variable spellings: compression/deep flags, representation provider/model/dimension, admitted scope-plan digest, and external owner digest. Native agreement requires the exact stored profile digest, compression disabled, deep memory disabled, the exact descriptor and core witness, `ACTIVE_CORE/NATIVE_ACTIVE`, and the actual qualified SQLite runtime `3.53.4`.

The resolver is pure: it creates no marker, selector, Fabric, writer, capability, core sidecar, or state transition. Its core inspection uses a qualified read-only connection with no WAL setup. It is intentionally safe to call repeatedly at startup and returns `REFUSED` rather than silently falling back after durable authority disagreement.

## Qualification evidence

`tests/test_b5_a2_deployment_fence.py` covers C0–C6 pre-selector, legacy, pending, active-core/external-pending, exact native-agreement, and mismatch dispositions; marker/selector absence and corruption; controlled-core containment and unselected claims; profile and runtime drift; selector/core ordering; retry/idempotency and safe abort; active-core staging-binding rejection; resolver side-effect freedom; and dynamic public REST/MCP inertness.

Ordinary `torment` requalification passed: 15 B5-A2 fence tests, 77 focused native binding/routing/post-write/trace tests, 23 native query tests, 279 public legacy regression tests, and 48 MCP regression tests. No public backend selection was added during those runs.

## Explicit non-authorizations

This slice does not authorize or implement admission/migration, public native activation, backend switching, routing a public request through the resolver, dual read/write, native-to-legacy rollback, restart cutover, public selector configuration, or changes to kernel/cognition semantics. Those remain later, separately authorized B5 work.
