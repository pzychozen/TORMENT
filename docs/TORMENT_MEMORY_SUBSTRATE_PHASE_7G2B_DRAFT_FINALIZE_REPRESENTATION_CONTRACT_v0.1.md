# TORMENT Memory Substrate — Phase 7G2B Draft / Finalize / Representation Contract v0.1

7G2B replaces the useful semantic purpose of legacy `spawn_memory → enrich →
flush_node` with an in-process draft followed by native finalization.  It does
not recreate legacy pre-commit residue.

`NativeMemoryCompatibilityFacade.begin_memory_draft` returns an immutable
`MemoryDraft` with an ephemeral `draft_token`.  The token is only process-local
workflow identity: it is not an object ID, revision ID, EID, transition ID, or
operation ID.  Draft creation and `enrich_memory_draft` run semantic validation
only.  They make no object, alias, revision, operation, transition, or
representation rows.  `abandon_memory_draft` is an explicit no-op discard.
The draft deliberately has no `eid` field.  Its exposed payload mappings and
sequences are frozen, and enrichment returns a replacement draft.

Enrichment returns a replacement draft and deterministically merges only
flexible content such as symbols, resonance, motifs, and physics fields.
Scope, lifecycle, governance, authority/authorization, provenance, revision,
representation/readiness, integrity, reconciliation, and operation/transition
shadows are refused with the 7G2A boundary.  Candidate-shaped summary and
immediate payload values are refused before a usable draft is returned.

`finalize_memory_draft` is the first durable boundary.  It derives a stable
`SOURCE_FINALIZE` sub-identity from the caller's supplied idempotency namespace
and key, then reuses 7G2A `create_memory_state`.  That one native transaction
allocates the EID and publishes the UUID object, R1, current pointer, alias,
native transition, object effect, and durable output.  Equivalent draft
reconstruction with the same caller identity recovers that result even after
the original Python draft or response is lost; changed final source intent
conflicts.

An optional `CompatibilityEmbeddingPublicationRequest` contains already
derived immutable bytes and explicit native representation facts.  7G2B never
calls an embedder.  `prepare_memory_draft_embedding` recovers/finalizes source,
creates PENDING against the exact returned R1, and establishes the SHA-256
expectation before any payload is accepted.  `finalize_memory_draft` then uses
the existing native READY operation to publish exact bytes, a MATCH
measurement, and READY/USABLE.  Representation PENDING, expectation, and READY
have separately derived stable operation identities, so retries do not create
another representation generation.

Source and representation are intentionally separate commits.  A dependency,
integrity, or READY failure leaves source committed and representation PENDING
unless the existing explicit failure operation marks it FAILED/WITHHELD.  No
source rollback occurs.  A later R2 does not retarget an R1-bound embedding.
Metadata-only representation reads remain payload-free; explicit usable reads
load bytes.

Invariant ownership remains frozen: source finalization uses the 7G2A native
object path (H1 current pointer, H2 typed effect, H3 rejection XOR result, H8
published output); representation PENDING/READY uses the native representation
path (H2/H4/H8 and immutable H5 evidence).  7G2B creates no reconciliation
state (H6 not applicable) and no legacy admission (H7 not applicable).

Bounded current-caller check (no production changes were made):

- `torment_service/fabric.py` lines 3499–3617 currently needs the legacy EID
  before flush for motif attachment, in-memory symbol/resonance enrichment,
  and the old abort path.
- `torment_service/character.py` lines 347–401 and 616–647 currently needs it
  before flush for motif membership and seed/drift workflows.
- `torment_service/promotion.py` lines 309–324 spawns then immediately flushes;
  it does not require pre-finalization enrichment identity.

These sites remain on current MemoryGraph behavior.  Their adaptation is
deferred; 7G2B does not create a durable EID reservation to accommodate them.

Deferred and absent in this slice: drop-in `spawn_memory(...)->eid`, drop-in
`flush_node(eid)`, compatibility links/relationships, search, embedding
generation, JSONL or event emulation, trajectory/world side effects, dual
write, MemoryGraph/Fabric/compression/embedding-store wiring, production core
creation, and cutover.  Tests use temporary qualified STAGING cores only.
