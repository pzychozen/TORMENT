# 7G5E4D E1 — integrated direct shared ingest and vector freshness

## Boundary

E1 is a qualification-only composition.  `NativeDirectSharedIngestAdapter`
accepts already-determined Fabric pre-write facts and a `shared` route request,
then uses `NativeFabricMemoryRouter` for the source write and a prepared
`NativeFabricPostWriteAdapter` for the tail.  It is not imported by
`TormentFabric`, provides no selector, and cannot fall back to legacy after a
native mutation.

The profile is named
`core_staging_with_shared_integrated_default()` and is usable only when:

```text
shared_integrated_default = QUALIFIED
compression = UNSUPPORTED
deep_memory = UNSUPPORTED
owner._compress_enable is exactly False
```

The preflight occurs before `NativeFabricMemoryRouter.route`.  A true
`owner._compress_enable` raises
`E1 integrated profile requires TORMENT_COMPRESS_ENABLE=false before effects`;
therefore it cannot leave a source, revision, representation, motif,
membership, or external-owner effect behind.

## Frozen corrected shared order

For a newly-created direct shared source, the E1 trace is:

```text
contradiction surface (shared predicate/no-op)
→ SRG collision (existing process-local law)
→ Hivemind packet/telemetry
→ M1 maintenance and qualified M2 merge decision
→ D0 anchor emission no-op
→ D0 anchor refinement no-op
→ D1 private-target mood drift (optional)
→ D3 native-world trajectory genesis/advance plus external evidence
→ D5A Character NOT_APPLICABLE_SCOPE
→ D4 external checkpoint snapshot
→ D6 disabled-compression no-op
→ ordinary shared proposal gate/no-op
→ B1 bridge suggestion
```

D3 occupies the created-memory world slot.  On a non-created context the
ordinary native world step occupies that slot instead.  The source router
already owns its source-world registration; E1 does not add another writer.

Existing failure topology is retained: SRG, Hivemind, M1, D0, D1, D3,
Character, and D4 keep their existing fail-soft boundaries.  B1 retains its
existing propagating bridge failure boundary.  E1 does not merge any of those
boundaries or introduce a compensating legacy tail.

## Storage and owner ledger

The direct source request is forwarded to `NativeFabricMemoryRouter` without
embedding or pre-write-fact recomputation.  Shared routing never takes the
private duplicate/reinforcement branch, so every accepted shared write has
`reinforced=False`.  The resulting context copies the request's summary,
type/class, strength, confidence, half-life, raw float32 input, provenance,
governance, lifecycle, links, motif result, and compatibility EID witness.

| Concern | Owner after E1 |
| --- | --- |
| Source, revision, READY representation, motifs, memberships | Native SQLite through the existing router |
| M1/M2 workflow suggestions | Existing motif-maintenance workflow owner |
| D0 anchors and D1 affect state | Existing derived-memory side store |
| D3 trajectory artifacts | Existing external trajectory owner |
| Character state/seed | Existing CharacterStore; shared trigger reads no seed |
| Checkpoints | Existing checkpoint writer; non-authoritative to native recovery |
| Hivemind packets/proposals | Existing Hivemind field and bridge owners |
| Cross-domain bridge suggestions | Existing BridgeRegistry with read-only native geometry |

No legacy memory or motif shadow state is introduced, and neither native core
nor vector runtime assumes ownership of those external artifacts.

## READY representation to vector lane ledger

E1 takes explicitly injected, already-warm `NativeMemoryVectorRuntime`
instances.  Their lane identity is the full native runtime scope plus the
representation-lane identity; there is no global vector owner.

| READY effect | Invalidate |
| --- | --- |
| Accepted shared research source | Shared research lane |
| D1 creates private aria mood source | Private aria lane |
| M1/M2 only, D0 no-op, D3, D5A, D4, D6, D2, B1 | No memory-vector lane |

Before the operation the seam records each warmed snapshot's EID set.  It
invalidates only a callback-reported READY EID absent from that lane's prior
snapshot, and deduplicates by complete lane key.  Thus exact retries whose
recovered EIDs are already in a rebuilt snapshot cause no second invalidation
or rebuild.  If a first response is lost while a lane remains dirty, it is
already not current and its next search rebuilds from SQLite; E1 never claims
that a non-READY or unobserved representation is current.

## Qualification evidence

`tests/test_substrate_native_integrated_direct_shared_ingest.py` exercises:

- the complete instrumented created-source trace, source compatibility view,
  READY representation, D0/D5A scope repairs, and single-lane counter result
  (`research: 1 → 2`, `aria: 1`, `engineering: 1`);
- deterministic D1 mood creation and two-lane freshness
  (`research: 1 → 2`, `aria: 1 → 2`, `engineering: 1`), with no bare source
  relation in the private mood payload;
- compression pre-effect refusal and an unclaimed-domain pre-effect refusal;
- an interruption after source commit, exact router recovery, and a completed
  lost-response retry with no duplicate source/mood representation or stale
  lane rebuild;
- injected M1, mood, trajectory, checkpoint, and Hivemind failures continuing
  to the later consumers, while the injected B1 failure propagates only at its
  existing final boundary; and
- cold reopening of SQLite, admitted scopes, fresh vector readers, motif and
  membership truth, the private mood source, and reloaded external D1 state.

The E1 fixture warms the required private aria, shared research, and shared
engineering lanes before every direct operation.  It also proves engineering
memory, motif, and vector state stay unchanged when research is written.

The focused E1 file completed with **6 passed**.  The bounded E4D-chain suite
(provenance, proposal materialization/orchestration, motif composition and
maintenance, native post-write, D0–D6/B1, routing, vector, E4C recovery, and
E1) completed with **187 passed, 12 skipped in 42.10s**.  The separate public
legacy post-write/motif/contradiction regression completed with **14 passed in
2.09s**.

## Status after E1

```text
PUBLIC_INGEST_BACKEND = LEGACY
FABRIC_QUERY_NATIVE_WIRED = NO
PRODUCTION_SELECTOR_ADDED = NO
NATIVE_ACTIVE = NO
DUAL_WRITE = NO
DUAL_READ = NO
CUTOVER_OPENED = NO
KERNEL_FILES_CHANGED = 0
KERNEL_MATHEMATICS_CHANGED = NO
```

E1 opens no E4E query integration work.
