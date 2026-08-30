# TORMENT Memory Substrate — Phase 7G5A3C2

## Atomic native new-memory and motif composition

Phase 7G5A3C2 introduces an unwired, schema-v1.1-only staging primitive:
`NativeMemoryMotifCompositionService`.  It is not selected by Fabric,
`DomainRouter`, Character, runtime binding, application startup, or any
production core path.

The primitive replaces the legacy new-memory partial-write shape with one
native semantic operation and one `BEGIN IMMEDIATE` / commit boundary:

```text
ordinary LEGACY_CORE_NODE R1 + scoped EID alias
  + exact closed provenance child
  + exact explicit R1 governance child
  + DERIVED_MOTIF R1 or one motif successor
  + identity-bound MOTIF_MEMBERSHIP R1
  -> one semantic transition
  -> three typed effects and three durable outputs
```

The output roles and ordinals are fixed: `MEMORY` / 0, `MOTIF` / 1, and
`MOTIF_MEMBERSHIP` / 2.  Provenance and governance are closed children of the
published memory revision, not independent semantic outputs.

## Preview is separate from commit

`prepare_plan()` reads the current native motif catalog and performs only pure
work:

```text
incoming candidate
-> current ordered catalog
-> attach/create decision
-> prospective motif state
-> prospective field
-> symbol/resonance enrichment patch
```

`commit()` does not re-run the cognitive choice.  It receives the immutable
plan and first verifies its complete catalog witness under the sole semantic
transaction.  The witness is lexicographically ordered by runtime motif ID
and holds each current runtime ID, object UUID, revision UUID, and revision
ordinal.  Added or removed motifs, a changed current revision, changed alias
target, changed selected motif, or changed order refuse the plan with no
composition residue.  This protects both ATTACH and CREATE.

A lost-response retry may re-read a newer catalog.  When the caller-provided
semantic input contract still matches the already committed operation, the
service returns the durable outputs instead of repeating work.  A changed
memory input, provenance, governance vector, embedding bytes/dimension,
motif configuration, or symbol context conflicts under the same idempotency
identity.

## Allocation compatibility

Memory EIDs are allocated inside the semantic transaction as the next scoped
committed `EID` alias.  New motif runtime IDs are derived from committed
runtime IDs using the legacy numeric-group rule:

```text
max(re.findall(r'(\d+)', motif_id)) + 1
motif_<domain>_<counter:04d>
```

Thus `motif_research_0003_split0008` contributes `8`, and the next research
runtime ID is `motif_research_0009`.  No mutable counter is reserved or left
behind on rollback.

## Geometry and prospective field

Representation retrieval stays separate from geometry:

```text
current qualified raw float32 embedding -> legacy-compatible motif _unit()
incoming request embedding -> decision-layer legacy-compatible _unit()
both -> shared motif radius calculation
```

Existing members with no current qualified `COMPAT_EMBEDDING` remain members:
they count toward prospective membership but are skipped as geometry samples.
The incoming request vector remains available prospectively before it has any
persisted representation.  The shared helper's current zero-vector semantics
are retained exactly: zero is a valid geometry input, and a one-member
zero-vector prospective motif currently measures radius `1.0`.

The pure field result is passed through the existing symbol and resonance
helpers to produce an R1 flexible-payload enrichment patch.  A3C2 never
writes symbol-state files, workspace JSONL, MemoryGraph state, or motif JSON.

## Representation and links are deliberately excluded

```text
A3C2 DOES NOT PUBLISH EMBEDDING REPRESENTATION.
QUALIFIED_LINK_PUBLICATION_IN_A3C2 = NO.
```

After a successful source/motif commit, the new memory can validly have no
representation.  A later, distinct representation operation establishes its
expectation and publishes PENDING/READY/FAILED state.  Raw unresolved links
and qualified link intents are separately inspected and rejected/deferred;
no string-to-EID guessing or relationship publication occurs here.

## Split boundary

Native split application is not implemented.  Legacy invokes its full split
logic after an attach.  A3C2 therefore uses a deterministic conservative gate:
when an ATTACH would make the motif reach the legacy auto-split eligibility
size (`AUTO_SPLIT_ENABLE` and prospective member count at least 96), it
refuses `UNSUPPORTED_NATIVE_SPLIT` before any A3C2 semantic state is written.
It does not execute or approximate native 2-means, split, merge, or
reconciliation.

## Failure semantics

Any failure after provenance, governance, memory insertion, motif mutation,
or membership insertion rolls back the entire A3C2 transaction.  The source
cannot survive independently of the motif change.  H1 current pointers, H2
typed effect completeness, H5 closed immutable revisions, H8 output/effect
agreement, and the A3C1S governance-child closure are validated before
commit.

This is a correctness correction over legacy pre-flush residue; it does not
alter legacy motif or MemoryGraph behavior.
