# TORMENT Memory Substrate — Phase 7G5A3A Fabric Motif Runtime Boundary v0.1

## Scope

Starting commit: `7abcfac791a2da408e5f5bbc577eae739a0ab947`.

This slice extracts the motif-facing boundary of the ordinary new-memory path
in `TormentFabric.ingest()`. `LegacyMotifRuntimeAdapter` remains a direct
delegating wrapper around the existing `MotifRegistry`; it is not a backend
selector and does not make native storage active.

## Converted ordinary-ingest locations

The one ordinary `spawn_memory()` path now calls the boundary for:

- attach-or-create mutation and its affected/created runtime IDs;
- whole-domain coherence-field projection; and
- entropy / merge-suggestion maintenance.

The execution order is unchanged: spawn memory, mutate motifs, project the
coherence field and calculate symbols, enrich resonance, flush the node, then
run the existing later maintenance. The response still exposes the legacy
runtime motif IDs and created-motif value.

`project_coherence_field_rows()` preserves `MotifRegistry.motifs.items()`
order, list-shaped centroid/member values, and the registry's exact
`_motif_radius()` result. It neither sorts nor caches rows.

## Legacy and staging status

The legacy registry remains live persistence and runtime authority. Its JSON
save/event behavior, duplicate member append behavior, tie and threshold
handling, split behavior, radius calculation, and maintenance equations are
not copied or changed.

The Phase 7G4 native runtime binding remains inert. This boundary imports no
native substrate service, adapter, connection, or SQLite component, creates no
database, and has no native selection or activation logic. Existing inert
binding coverage continues to prove that ordinary Fabric remains legacy-only
even when an inert staging binding is supplied.

## Explicitly unresolved

- Character motif routing remains unchanged and still receives the legacy
  registry outside this converted ordinary-ingest block.
- Native motif enumeration order, radius semantics, runtime-ID allocation, and
  native membership/finalization ordering are not defined by this slice.
- Native auto-split application is not implemented.
- No Fabric native ingest, dual write/read, migration, reconciliation, cutover,
  or activation is introduced.

## Verification

Focused tests cover adapter delegation across create/attach/threshold/tie/
duplicate/split outcomes, exact whole-domain projection order and rows, and
ordinary-ingest ordering through motif mutation, field projection, one flush,
and later maintenance. The release run uses `torment-substrate` with Python
3.11.15, sqlite3 module 2.6.0, and SQLite 3.53.4.
