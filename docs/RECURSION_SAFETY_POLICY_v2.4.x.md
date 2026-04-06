# TORMENT 2.4.x — Recursion-Safety Policy for Archivist-Origin Memories

## Purpose

Prevent Archivist write-back from creating self-reinforcing cognition loops
while still allowing bounded, provenance-aware memory formation in the future.

## Core Rule

A memory created by Archivist write-back must not be used as direct source
material for another Archivist write-back in 2.4.x.

## Policy Rules

### Rule A — Direct Recursion Block
If any `parent_eids` reference a memory whose provenance has
`source_role == "archivist_writeback"`, reject the write-back.

### Rule B — Multi-Parent Strict
If a proposal is derived from multiple parents and ANY parent is
Archivist-origin, the proposal is not eligible. Not majority-based — any
single archivist parent blocks.

### Rule C — Missing Provenance
If any parent memory lacks readable provenance, treat as unknown.
Unknown provenance = not safe for Archivist write-back.

### Rule D — Retrieval Visibility
Archivist-origin memories may appear in retrieval. They must be marked
so the write-back stage can refuse them as parents. Retrieval is allowed;
write-back eligibility is restricted.

### Rule E — Generation Depth
If a memory has `source_role == "archivist_writeback"`, its effective
Archivist depth is 1. No memory with depth >= 1 may be used as parent
for another write-back.

### Rule F — No Laundering
Archivist-origin memories do not become eligible again through
reinforcement, resurfacing, re-retrieval, summarization, or movement
through other subsystems. Provenance describes origin, not latest actor.

## Safe Parent Classes (First Pass)

Allowed: `user_input`, `tool_result`, `memory` (migrated/imported)
Not allowed: `role_output` with archivist source, `derived` (unless reviewed), `spirit_reflection` (deferred)

## Rejection Reasons

- `archivist_parent_blocked` — parent has archivist-origin provenance
- `unknown_parent_provenance` — parent lacks provenance or cannot be retrieved
- `unsafe_parent_source_type` — parent source_type not in safe set

## Enforcement Point

At write-back eligibility check time (pipeline step 4b), not at proposal
creation time. Order: retrieve → propose → inspect parents → decide → ingest.

## Implementation Status

- Rules A-F: implemented in `cognition/pipeline.py::_write_back_approved()`
- Parent inspection: via `lookup_fn` parameter (resolves parent EID → payload)
- Archivist write-back: remains gated behind `TORMENT_ARCHIVIST_WRITEBACK=0`
- Provenance schema: `torment_service/provenance_v1.py::ProvenanceV1`
- Debug surface: `GET /debug/provenance` endpoint
