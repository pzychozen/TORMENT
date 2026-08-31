# TORMENT Memory Substrate 7G5E2 — Character Native Continuity v0.1

## Boundary

7G5E2 closes the private-Character continuity blocker for qualified staging
cores only. It adds no Fabric selector, activation, dual read/write, cutover,
shared-domain behavior, or auto-split implementation.

CharacterStore remains external. In particular, seed.json and
character_state.json are neither migrated into SQLite nor treated as native
authoritative state. SQLite owns only the native core memories, motifs, and
READY representations referenced by the external seed.

## Frozen legacy writer witness

The witness is read from the real normal Character writer shape:

- seed.json identifies seed_id, character_name, ordered seed_eids, and
  seed_motif_id.
- each current private row proves type=seed_canon, canon=true,
  memory_class=core, tier=core_identity, the exact
  _split_seed_text(seed_text)[index] summary, source ownership, fixed
  strength/confidence/half-life, and protected system/canon_set lifecycle.
- the named legacy motif proves its exact current members and contains at
  least one witnessed seed EID.

The historical writer attaches concepts independently. It therefore does not
promise that every seed EID is in the one selected seed motif. The descriptor
records both all seed EIDs and the exact selected-motif seed-member subset;
7G5E2 never invents stronger legacy topology.

## Character-only provenance

No ProvenanceV1 vocabulary changed. A witness-qualified seed R2 and fresh
native seed R1 carry this fixed NativeProvenanceRecord:

| Field | Value |
| --- | --- |
| origin_kind | CHARACTER_SEED_PLANT |
| source_channel | character_runtime |
| source_role | seed_canon |
| derivation_status | seed_plant |
| uncertainty_state | KNOWN |
| memory_role | seed_canon |

Canonical descriptive notes bind the seed id, character name, concept index,
seed-definition digest, and writer-witness digest. Ordinary B2 still requires
its existing exact ProvenanceV1 evidence. Only a witnessed seed_canon R1
uses NativeMigrationCharacterSeedNormalizationService.

## Existing workspace profile and recovery

EXISTING_WORKSPACE_PRIVATE_CHARACTER is a separate admission profile. Its
descriptor binds the Character compatibility status, external seed definition
digest, seed EIDs, motif alias, exact selected-motif membership, and witness
digest. It does not freeze mutable character_state.json bytes.

After B2/B3A/B4A/B5, recovery requires the retained external CharacterStore
to reproduce the descriptor seed definition. Native namespace-bound readers
resolve every seed EID, READY qualified representation, and seed motif without
reading a legacy graph, nodes, embeddings, or motif file.

## Fresh native planting

NativeCharacterSeedPlantRuntime is an explicit Character-only writer. It uses
_split_seed_text, a caller-owned qualified embedder, Character seed
provenance, R1 source publication, and normal PENDING → expectation → READY
representation semantics. It returns stable seed EIDs and a seed motif id for
the external CharacterStore to persist only after COMPLETE.

The planter applies the legacy per-concept 0.50 motif attach/create decision
and preserves its seed-basin selection rule. A prospective attachment at the
legacy auto-split boundary refuses with
CHARACTER_MOTIF_SPLIT_PARITY_REQUIRED; it does not silently choose a
different topology. Partial plants resume by their durable source,
representation, motif-decision, and seed-basin-boost operation keys.

## Qualification evidence

The focused suite proves:

- exact writer witness acceptance and refusal for contradictory seed files,
  owner/name/id/index/summary mismatches, missing concepts, foreign
  seed_canon rows, and invalid selected-motif membership;
- Character-only normalization, B2 response-loss recovery, and ordinary-B2
  separation;
- normal python -m torment_service source production, Character admission,
  native cold recovery in a fresh process, and external-store continuity;
- seed EID/motif/READY representation resolution after legacy graph storage is
  unavailable;
- legacy versus native C1A drift output parity, and C1B deterministic,
  idempotent correction after cold recovery;
- fresh native planting, retry, partial resumption, changed-definition
  refusal, cold reopen, and prospective split refusal.

## Status

```text
BLOCKER_1_PRIVATE_CORE_CLOSED = YES
BLOCKER_2_CHARACTER_CLOSED = YES
BLOCKER_3_AUTO_SPLIT = OPEN
BLOCKER_4_SHARED_DOMAIN = OPEN
BLOCKER_5_SELECTOR = OPEN

CHARACTERSTORE_REMAINS_EXTERNAL = YES
PROVENANCE_V1_CHANGED = NO
PRODUCTION_SELECTOR_ADDED = NO
NATIVE_ACTIVE = NO
DUAL_WRITE = NO
DUAL_READ = NO
CUTOVER_OPENED = NO
```
