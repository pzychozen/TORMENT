# Blocker-5 A4R2 — Native Public Ingest Recovery Envelope

## Verdict and boundary

```text
B5_A4R2_NATIVE_PUBLIC_INGEST_RECOVERY = QUALIFIED
PUBLIC_PRE_COGNITION_IDEMPOTENCY_RECOVERY = QUALIFIED
PUBLIC_MUTATION_RESERVATION = QUALIFIED
COGNITION_STARTED_FENCE = QUALIFIED
PREPARED_INGEST_DURABLE_RECEIPT = QUALIFIED
PREPARED_INGEST_REHYDRATION = QUALIFIED
NATIVE_PUBLIC_INGEST_STORAGE_ADAPTER = QUALIFIED
NATIVE_PUBLIC_POST_WRITE_RECOVERY = QUALIFIED
PUBLIC_COMPLETION_RECEIPT = QUALIFIED

PUBLIC_NATIVE_EXECUTOR = QUALIFIED_PRIVATE_DIRECT_USE
PUBLIC_NATIVE_TRANSPORT_WIRING = NO
B5_A4_PUBLIC_BACKEND_SELECTION = BLOCKED
```

This is a qualification-only recovery envelope for an already-admitted
`NativeProductionResourceOwner`.  It is not imported by REST, Spine, MCP,
startup, or a public selector.  No public endpoint changes backend in this
slice.

```text
PUBLIC_INGEST_BACKEND = LEGACY
PUBLIC_QUERY_BACKEND = LEGACY
PUBLIC_NATIVE_SELECTION = NO
DUAL_WRITE = NO
DUAL_READ = NO
REAL_CUTOVER = NO
CORE_SCHEMA_CHANGE = NO
NEW_SIDE_DATABASE = NO
KERNEL_FILES_CHANGED = 0
```

## Receipt contract and namespace

`NativePublicMutationReceiptStore` writes evidence only to the existing
native-core `operations` ledger.  It uses the admitted private agent scope's
already-existing `idempotency_namespace_id` before any later shared-domain
routing:

```text
PUBLIC_RECEIPT_NAMESPACE = admitted private-agent idempotency namespace
PUBLIC_MUTATION_RECEIPT_DATABASE = existing native core
```

This namespace owns retry evidence only.  It neither changes memory scope nor
grants authorization.  Every receipt has an immutable canonical intent and a
stable phase key:

```text
NATIVE_PUBLIC_MUTATION_RECEIPT:RESERVED:<public-native-key>
NATIVE_PUBLIC_MUTATION_RECEIPT:COGNITION_STARTED:<public-native-key>
NATIVE_PUBLIC_MUTATION_RECEIPT:PREPARED:<public-native-key>
NATIVE_PUBLIC_MUTATION_RECEIPT:COMPLETE:<public-native-key>
```

They publish no semantic transition, object/revision, representation, target,
or output.  The focused ledger test proves four receipt rows and zero receipt
transitions/outputs.

`RESERVED` binds the native core UUID, workspace, agent, `ingest`, the R1
`public-mutation/v1` derived native key, canonical public request fingerprint,
and identity-contract version.  It never stores the raw caller key.  A changed
fingerprint is rejected as `PUBLIC_IDEMPOTENCY_CONFLICT` before cognition.

## Recovery matrix

| Durable evidence, checked in order | Result | Retry behavior |
|---|---|---|
| `COMPLETE` | `COMMITTED_SAME_REQUEST` | Return the exact stored response dict; no cognition, storage, or post-write. |
| `PREPARED`, no `COMPLETE` | `INCOMPLETE_RECOVERABLE` | Rehydrate and resume native storage/post-write only. |
| `COGNITION_STARTED`, no `PREPARED` | `COGNITION_OUTCOME_UNCERTAIN` | Fail closed with `RECOVERY_REQUIRED`; never rerun cognition. |
| `RESERVED` only | `NEW` | Safely persist `COGNITION_STARTED`, then call preparation once. |

The marker is written immediately before the existing Fabric preparation
call.  Thus:

```text
COGNITION_STARTED_WITHOUT_PREPARED != SAFE_TO_RETRY_COGNITION
AMBIGUOUS_COGNITION_REEXECUTION = NO
```

`COMPLETE` binds both reservation and prepared digests, fingerprint, native
key, and the canonical public response.  An existing completion must match the
attempted immutable result exactly; malformed or mismatched receipt linkage is
refused.

## Prepared carrier and native execution

`PreparedFabricIngest` is still produced by the one existing
`TormentFabric.ingest(..., _prepare_only=True)` preparation path.  R2 adds no
second cognition implementation.  The carrier is serialized as
`TORMENT_PREPARED_FABRIC_INGEST_V1`: finite little-endian float32 bytes,
dimension, base64 payload, SHA-256 witness, plus all frozen storage,
post-write, response, affect/phase/SRG, symbolic, retention, and write-gate
facts.  Decode checks schema, byte length, digest, dimension, and finite
vector validity before it rehydrates a detached immutable carrier.

`NativeFabricIngestStorageAdapter` turns that carrier into the existing
`NativeFabricRouteRequest` under
`NativeProductionResourceOwner.open_write_context()`.  Its storage child key
is `<public-native-key>:STORAGE`.  No-write returns a normalized `NO_WRITE`
outcome without entering the router.  Writes retain the qualified native
reinforcement/new-memory, motif, READY representation, and compatibility-EID
laws.  Native object UUIDs stay in the internal route witness.

Caller `extra_payload` is projected with legacy's internal-wins discipline:
typed scope/provenance/governance/lifecycle facts cannot be shadowed by an
ordinary payload key.  The regression covers attempted `scope`, `provenance`,
and `governance` shadows.

After storage, the executor calls the existing B5-A3
`NativeProductionPostWriteContext` / `NativeFabricPostWriteAdapter`.  It
introduces no public-specific post-write algorithm.

## Source and post-write recovery

R2 exposed and closed a restart-sensitive routing gap: a completed new-memory
source could previously be encountered by a duplicate search before its source
receipt was recovered, creating a reinforcement revision on retry.  The
router now reconstructs the same A3C2 composition request, validates its
stored retry contract, and recovers its completed source before duplicate
selection.  Its representation publication uses the original idempotent child
keys.  This preserves source identity across process-local owner recreation.

The focused tests cover:

```text
W0  RESERVED -> retry runs cognition once
W1  COGNITION_STARTED before body -> fail closed
W2  preparation interruption -> fail closed
W3  PREPARED retry -> no re-cognition, including owner recreation
W4  source commit -> source recovery, including owner recreation
W5  interruption after native post-write world step -> restart convergence;
    no extra memory/revision/relationship/representation, only COMPLETE
W6  post-write complete before public completion -> convergence then COMPLETE
W7  COMPLETE/lost response -> exact response replay, including owner recreation
```

They also prove soft write-gate draw count one, no-write replay, native new
memory and reinforcement replay, changed text/step/vector/scope-domain
conflicts before cognition, receipt-only ledger effects, and shared-source
replay.  The direct executor guards legacy `MemoryGraph` search, spawn, flush,
and mutation: none are used as memory authority.

## Remaining boundary

R2 does not select a public backend or activate native public transport.  A
separately authorized `B5-A4R3 — public backend selection / transport wiring`
would need to consume this recovery envelope for REST, Spine, and MCP; it must
not reimplement identity, receipts, or recovery.
