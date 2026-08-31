# TORMENT Memory Substrate — 7G5E1 Existing-Workspace Native Recovery

## Status

This slice closes only the bounded Blocker-1 profile:

```text
EXISTING_WORKSPACE
PRIVATE_AGENT
ORDINARY_CORE_MEMORY
CHARACTER_FREE
SINGLE_EMBEDDING_LANE
```

It is an admission and native-read recovery qualification. It does not add a
production selector, native activation, dual write, dual read, or cutover.

## Boundary

`ExistingWorkspaceNativeAdmissionService` is a substrate/migration coordinator.
It imports neither the D1 `experiments/` builder nor `torment_service.fabric`.
It composes existing evidence admission, B1 readiness, B2 normalization, B3A
captured-vector bootstrap, B4A lane-preserving motif projection, and B5
readiness. B3B/B4B are not selected: a re-embedding requirement refuses this
single captured-lane profile instead of inventing an embedder or geometry.

The caller supplies the source namespace and key; identity, semantic, motif,
membership, and idempotency namespaces; the target lane; and B5’s retained
side-store observations and inert post-write configuration. No EID text is
used to infer a namespace, and reopening uses the descriptor’s same explicit
identities rather than generating replacements.

## Source and snapshot contract

First admission requires a nonexistent `.db` destination distinct from the
legacy workspace. The source is never converted in place. The descriptor,
snapshot package, and manifest must all sit outside the workspace root.

The source fingerprint covers every regular source-workspace file. It is
checked when first captured, on every resume, and before a completed result is
returned. A changed source refuses with
`EXISTING_WORKSPACE_SOURCE_EVIDENCE_MISMATCH`.

The snapshot carries the selected private node log, embedding evidence,
workspace lane lock, and selected motif registry. Its node snapshot is the
legacy current-state projection only:

```text
append-only nodes.jsonl
→ final record for each EID
→ ordered by first surviving EID appearance
```

This is the existing `MemoryGraph` current-state rule, not a new revision or a
semantic rewrite. It matters for reinforced memories: one current EID may have
several source node-log records but one embedding-map row. Freezing duplicate
node references would incorrectly attempt to admit that one map record twice.
The source bytes and embedding bytes remain unchanged.

Sources with a Character seed/state refuse explicitly with
`EXISTING_WORKSPACE_CHARACTER_PROVENANCE_BLOCKED`. A claimed shared scope
refuses with `SHARED_DOMAIN_ADMISSION_NOT_IN_7G5E1_PROFILE`. Motifs at or above
the legacy auto-split minimum (96 members) refuse rather than being simplified
or retired.

## Durable descriptor and retry

The canonical JSON descriptor records its schema/version, bounded profile,
admission key, source fingerprint, snapshot identity and manifest digest,
source namespace/key, workspace and agent IDs, native core ID, schema version,
scope-plan digest and IDs, lane, B-stage witnesses, B5 report digest, and
completion state. The wrapper’s SHA-256 covers the canonical payload; malformed
or changed descriptors refuse before recovery.

States are explicit:

```text
ADMISSION_NOT_STARTED
ADMISSION_INCOMPLETE_RESUMABLE
ADMISSION_COMPLETE
RECOVERY_REFUSED
RECOVERY_READY
```

The coordinator writes an incomplete descriptor before opening a new core.
Each B-series operation retains its established semantic idempotency key. A
response loss after a committed B2/B3A/B4A operation, or a process interruption
between stages, resumes against the same snapshot and creates no duplicate
objects, revisions, aliases, representations, motifs, memberships, or
operations. No retry deletes or recreates the destination.

## Cold native recovery

`recover_existing_workspace_native_runtime()` accepts only a core path and the
complete descriptor. It validates the exact STAGING core identity and
`LEGACY_ACTIVE`/null-reference deployment metadata, reconstructs
`NativeMemoryRuntimeScope`, `NativeFabricRoutingScope`, and the lane, then
opens only:

- `NativeMemoryCompatibilityFacade`
- `NativeCompatEmbeddingReader`
- `NativeMotifRuntimeReader`
- `NativePostWriteMemoryAccess` (read-only runtime enumeration/projection)

The recovered object has no write selector, Fabric mutation capability, source
path, snapshot path, `MemoryGraph`, or fallback admission path. Fresh-process
qualification succeeds after the disposable source workspace is made
unavailable.

## Read qualification

Focused tests cover eight synthetic current private memories, a repeated
reinforced source record, two lane-preserving motifs, raw captured float32
bytes, full compatibility projections (including type/class, strength,
confidence, half-life, governance, and provenance), runtime order carriers,
exact native primitive cosine search, stable motif alias ordering, member
closure, radius reads, B5 retained-side-store observations, incomplete-recovery
refusal, descriptor tamper refusal, wrong core/lane refusal, source-change
refusal, Character refusal, and shared scope refusal.

The production-shaped fixture starts normal `python -m torment_service` with
Character disabled, uses normal HTTP workspace/agent/ingest surfaces to create
eight ordinary private memories plus a reinforcement, stops it, and admits the
resulting existing workspace. Its native readers still work in a fresh Python
process after the legacy workspace is unavailable.

## Explicit exclusions

```text
BLOCKER-2 Character                     OPEN
BLOCKER-3 motif auto-split              OPEN
BLOCKER-4 shared-domain                 OPEN
BLOCKER-5 production selector/cutover   OPEN

NATIVE_ACTIVE = NO
DUAL_WRITE = NO
DUAL_READ = NO
CUTOVER_OPENED = NO
```

Checkpoint and trajectory evidence remain external owners. B5 observes their
typed retained-side-store compatibility; this slice does not move either into
SQLite.
