# Blocker-5 A4R1 — Public Mutation Identity and Ingest Orchestration

## Scope and disposition

This bounded slice closes two prerequisites discovered in the B5-A4 public
selection preflight:

```text
PUBLIC_CALLER_IDEMPOTENCY_CONTRACT = QUALIFIED
BACKEND_NEUTRAL_INGEST_PREPARATION = QUALIFIED
LEGACY_INGEST_STORAGE_ADAPTER = QUALIFIED
LEGACY_PUBLIC_INGEST_PARITY = PASS

B5_A4_PUBLIC_BACKEND_SELECTION = BLOCKED
PUBLIC_PRE_COGNITION_IDEMPOTENCY_RECOVERY = BLOCKED
```

It does not select, construct, start, or route to a native public backend.
The current public surfaces remain:

```text
PUBLIC_INGEST_BACKEND = LEGACY
PUBLIC_QUERY_BACKEND = LEGACY
PUBLIC_NATIVE_SELECTION = NO
NATIVE_PUBLIC_OWNER_CONSTRUCTION = NONE
DUAL_WRITE = NO
DUAL_READ = NO
REAL_CUTOVER = NO
```

No kernel file or kernel algorithm changed.

## Public mutation identity

`PublicMutationKey` is the single, opaque optional retry identity.  It is
accepted as `Idempotency-Key` on the existing REST ingest and tool-result
ingest endpoints, and as `SpineRequest.idempotency_key` on Spine/MCP.  REST
without the header preserves the previous request path unchanged.  The key is
non-empty when present, at most 256 characters, rejects ASCII control
characters, is never path-interpreted or logged, and is preserved exactly
without trimming or case folding.

`task_id` remains trace/governance identity.  Its current auto-generation is
unchanged, and it is not translated into a mutation key:

```text
TRACE_IDENTITY != IDEMPOTENCY_IDENTITY
TASK_ID_IS_IDEMPOTENCY_KEY = NO
```

The internal future-native identity is deterministic but does not expose the
caller token:

```text
public-mutation/v1/
  SHA256(canonical JSON of contract, operation, workspace, agent, caller key)
```

Thus the same public key through REST or MCP derives the same internal key
across restart, while the native namespace never receives the raw key.

The public request fingerprint is separately SHA-256 over canonical JSON of
the contract, operation, workspace, agent, and semantic ingest inputs.  It
covers text, logical step, scope/domain, supplied summary and embedding,
provenance, memory class, extra payload, and public ingest flags; timestamps
and `task_id` are deliberately excluded.  The frozen R2 law is:

```text
same key + same fingerprint      -> same logical public operation
same key + changed fingerprint   -> IDEMPOTENCY_CONFLICT
```

R1 does not enforce that law against legacy storage: doing so would change
legacy semantics without a safe recovery receipt.  It supplies the two stable
identities R2 needs to enforce it before cognition.

## Ingest boundary

`TormentFabric.ingest` continues to perform the existing cognition once:
kernel process, provenance and Character work, phase/SRG updates, role/affect,
embedding, domain routing, and write-gate decision.  It then creates immutable
`PreparedFabricIngest` facts: workspace/agent/scope/domain, logical step,
summary, detached read-only normal embedding, embedding identity/checksum,
memory facts, computed half-life, links, provenance, flexible/Tri/SRG/phase/
affect facts, write decision, motif threshold, packet flag, and the derived
identity/fingerprint when a public key was supplied.

The retained legacy graph/motif mutation body keeps its existing duplicate
search, same-class and contradiction guards, reinforcement, spawn/enrichment,
motif attach/create, symbol/resonance update, single flush, and atomic abort
order.  `LegacyFabricIngestStorageAdapter` converts that one legacy authority
result into `FabricIngestStorageOutcome` with immutable public-independent
facts:

```text
workspace / agent / scope / domain
NO_WRITE | REINFORCED_EXISTING | CREATED_NEW
stored / eid / motifs / created motif / state symbol / storage witness
```

Existing `FabricPostWriteContext` and `LegacyFabricPostWriteAdapter` consume
the normalized outcome, rather than making response assembly depend on the raw
storage booleans.  TORMENT retains all post-write owners: Hivemind, Character,
BridgeRegistry, conflict handling, trajectory/checkpoint, world, and SRG have
not moved into SQLite.

## Recovery archaeology and R2 blocker

The qualified native route has a narrow
`_recover_reinforcement_request(...)` lookup.  It reads a previously planned
`NATIVE_REINFORCEMENT:SOURCE:*` operation after the router is entered, then
recovers the reinforcement transition.  New-memory writes use
`NATIVE_FABRIC_NEW_MEMORY:SOURCE:*`, but there is no generic public-operation
reservation/receipt keyed by this R1-derived identity which can, before
`TormentFabric.ingest` cognition, distinguish:

```text
NEW
COMMITTED_SAME_REQUEST
CONFLICTING_REQUEST
INCOMPLETE_RECOVERABLE
```

Therefore a lost response retry could otherwise rerun kernel processing,
phase/SRG/role/affect work, embedding/routing, and the random soft write gate.
R1 must stop here:

```text
PUBLIC_PRE_COGNITION_IDEMPOTENCY_RECOVERY = BLOCKED
```

B5-A4R2 needs a durable public-operation reservation plus completion/recovery
receipt in the existing native operation evidence.  It must be keyed by the
derived native operation key and bind the public request fingerprint, be
inspectable before Fabric cognition, return a completed response for the same
fingerprint, reject a changed fingerprint, and expose a safe incomplete
recovery state.  No new side database is authorized or introduced by R1.

## Evidence

The R1 test set proves bounded/exact key validation, deterministic non-raw
derivation, canonical fingerprint behavior, trace/key independence, Fabric
carrier propagation, optional REST header handling, invalid REST/Spine/MCP
rejection before ingest dispatch, and the unchanged legacy graph authority.
It is run with the pre-existing legacy characterization suites covering
no-write, reinforcement, new-memory post-write order/outcomes and public
response shape.  The broader legacy suites additionally cover unknown-domain
atomicity, supplied embedding/provenance/tool-result lifecycle, contradiction,
MCP, and Spine behavior.

```text
KERNEL_FILES_CHANGED = 0
KERNEL_MATHEMATICS_CHANGED = NO
KERNEL_GEOMETRY_CHANGED = NO
KERNEL_VECTORISATION_CHANGED = NO
```

R2 is a separate authorization.  This document neither opens it nor resumes
B5-A4 public backend selection.
