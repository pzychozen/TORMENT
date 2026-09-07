# P3 Character seed witness composition qualification

## Authority and boundary

Starting revision: `1bd1973e57f5610dc23facb5ded46998fad9f53e`.

P2 Character-seed authority is the Envelope-C aggregate commitment opening:

```text
Envelope C: d97c0545a538efca9657119abac133efc010bc41191b35f9e74ce9885f79b34b
Aggregate:  971e6ddac04f438035ba856f34f365c5398af3598acf5947e8aaaa5b9e5ce0c6
Workspace:  hivemind-bounded-context-n5-v1-n5-20260825T220310Z-2af44f6c2e
Key:        seed:hivemind_n5_contrarian_fluid_v1
Digest:     fa2a1d9c2bd0782923993cb829cbe39328b2272f35878d8119142358866585f3
Proof:      AGGREGATE_COMMITMENT_OPENING
```

The predecessor P3 carrier omits Character witness descriptors.  This change
therefore adds a separate descriptor-only continuation carrier; it does not
rewrite the source-admission or completion carrier and makes no schema, P2,
selector, or real-root write.

## Implemented contract

Initial P3 Character composition requires all of the following:

- the opened P2 aggregate authority and exact `seed:<seed_id>` tuple;
- the exact frozen `seed.json` bytes, whose SHA-256 equals that tuple digest;
- the existing `CharacterSeedWitness` descriptor, reconstructed through
  `CharacterSeedWitness.from_descriptor_payload()`;
- a private P3 scope whose legacy namespace, workspace, agent, domain, and
  `seed_canon` EID set agree exactly with that witness.

Logical `seed_eids` stay unique.  In contrast, `seed_motif_member_eids` is
the exact ordered legacy occurrence sequence: it is non-empty, contains only
non-negative integers, and deliberately permits duplicates.  The persisted
`seed_motif_seed_eids` is its exact ordered projection onto the logical seed
membership set, so duplicate count and order are both bound by the witness
digest.  This is evidence-only: B2 still routes exactly once per logical seed
EID, and neither motif migration nor the ordinary provenance paths change.

The continuation carrier binds its predecessor B1/snapshot identity, snapshot
count and identity digest, Envelope C, aggregate, P2 observation key/digest,
and the existing descriptor.  It validates all of those facts on recovery.
After it exists, a retry reloads this descriptor-only carrier without another
read of seed bytes; an initial composition without those exact bytes refuses.

P3 B1 records an explicit `CHARACTER_SEED` normalization kind only for the
existing `CHARACTER_NORMALIZATION_WITNESS_REQUIRED` reason and a witnessed
EID.  B2 routes only that kind to
`NativeMigrationCharacterSeedNormalizationService`; deterministic and
structural-unknown rows remain on `NativeMigrationRuntimeNormalizationService`.
Thus a seed-shaped missing-provenance row cannot fall through the ordinary
unknown-original-provenance path.

## Disposable implementation result

The focused synthetic carrier run is qualified:

```text
CHARACTER_CONTINUATION_CARRIER = QUALIFIED (synthetic disposable source)
CHARACTER_B2_P3_ROUTING = QUALIFIED
CHARACTER_PRECEDENCE_OVER_UNKNOWN_PROVENANCE = QUALIFIED
CHARACTER_SEMANTICS_CHANGED = NO
CHARACTER_WITNESS_RULE_CHANGED = YES_RAW_MOTIF_OCCURRENCE_FIDELITY_ONLY
CHARACTER_LOGICAL_EID_OR_B2_MULTIPLICITY_CHANGED = NO
CHARACTER_PROVENANCE_CONTRACT_CHANGED = NO
CHARACTER_RUNTIME_BEHAVIOR_CHANGED = NO
KNOWN_PROVENANCE_PATH_CHANGED = NO
UNKNOWN_ORIGINAL_PROVENANCE_PATH_CHANGED = NO
MOTIF_MIGRATION_BINDING_CHANGED = NO
B3A_SEMANTICS_CHANGED = NO
B3B_SEMANTICS_CHANGED = NO
```

The disposable Character EIDs `101` and `102` produced the existing
`CHARACTER_SEED_PLANT` R2 provenance, recovered idempotently, and refused a
tampered predecessor B1 route.  Its complete carrier had three snapshots,
six canonical EIDs, `B3A=4`, `B3B=2`, `B4A=1`, `B4B=0`, and `B4C=3`; no B3/B4
operation was executed by that qualification.

Focused failures prove rejection for a P2 byte-digest mismatch, P2 observation
key mismatch, descriptor witness-digest mismatch, and changed predecessor
carrier identity.  Existing Character, runtime-readiness, ordinary/structural
unknown, motif, representation, and root-P3 regression suites remain part of
the broader selection.

## Exact-byte recovery and copied-real result

The narrowly authorized read of the one production `seed.json` file completed
without any write.  Its raw-byte SHA-256 matched the opened P2 observation
exactly and those unchanged 774 bytes were copied to the additive
administration evidence directory:

```text
SEED_COMMITMENT_OPENED = YES
RECOVERED_SEED_BYTE_EVIDENCE = C:\TORMENT\TORMENT_administration\character-seed-exact-byte-recovery-1bd1973-20260907\seed.json
SEED_CAPTURE_SHA256 = fa2a1d9c2bd0782923993cb829cbe39328b2272f35878d8119142358866585f3
P2_SEED_OBSERVATION_DIGEST = fa2a1d9c2bd0782923993cb829cbe39328b2272f35878d8119142358866585f3
```

The witness composition used only the recovered byte artifact, private
snapshot `c7c7911f-d752-4fdc-8c89-14d88745fcce`, and frozen research motif
artifact.  The copied motif bytes match the P3 snapshot manifest
(`841fe0f02942b786dbf9dcf0e6ccf096a835518a9f842f33043905df8cfb1a46`).
Its raw member sequence has 56 entries and 12 distinct EIDs; EIDs 1 and 2
each occur five times.  The qualified witness preserves all 56 occurrences
and has the exact projected seed occurrence sequence
`(1, 2, 1, 2, 1, 2, 1, 2, 1, 2)`.  The frozen motif was not deduplicated,
replaced, or otherwise reinterpreted.

The descriptor-only continuation binds the copied carrier's 154 snapshot
identities, predecessor identity, Envelope C, aggregate opening, P2 seed
tuple, and witness descriptor.  Copied-core B1 selection retained only the
logical Character EIDs 1 and 2 despite those ten motif occurrences.  Their
B2 writes use the established `CHARACTER_SEED_PLANT` route and idempotently
produced R2 revisions `ad54ec31-6932-4808-a3bb-5631c494c7b7` and
`ad6e94b2-14e2-48bf-80d2-ed4a51640018`; EID 4 remains the previously
qualified Phase-C ordinary result.  Existing B3A then completed for both
Character rows and left each runtime-ready.

```text
CHARACTER_WITNESS_FROM_FROZEN_EVIDENCE = QUALIFIED
CHARACTER_CONTINUATION_CARRIER = QUALIFIED_ONE_WITNESS
COPIED_EID_1_CHARACTER_B2 = QUALIFIED
COPIED_EID_2_CHARACTER_B2 = QUALIFIED
COPIED_EID_4_UNKNOWN_B2 = PREVIOUS_PHASE_C_RESULT_RUNTIME_READY_AS_IS
COPIED_SEMANTIC_FACTS_UNRESOLVED = CLEARED_FOR_EIDS_1_2
COPIED_CHARACTER_B2_LOGICAL_EID_COUNT = 2
B3A_CHARACTER_COUNT = 2
B3B_COUNT = NOT_EXECUTED_FULL_ROOT_P3_REQUEST_REQUIRES_UNOPENED_P2_MANIFEST
ADMITTED_MOTIF_COUNT = NOT_EXECUTED_FULL_ROOT_P3_REQUEST_REQUIRES_UNOPENED_P2_MANIFEST
B4A_COUNT = NOT_EXECUTED_FULL_ROOT_P3_REQUEST_REQUIRES_UNOPENED_P2_MANIFEST
B4B_COUNT = NOT_EXECUTED_FULL_ROOT_P3_REQUEST_REQUIRES_UNOPENED_P2_MANIFEST
B4C_COUNT = NOT_EXECUTED_FULL_ROOT_P3_REQUEST_REQUIRES_UNOPENED_P2_MANIFEST
```

The scoped copied-real Character continuation is **qualified**.  Full-carrier
B1/B2 closure and B3B/B4 derivation were not run: their `RootP3` request
requires the full P2 explicit-source manifest, which was not copied into this
qualification and may not be reopened from the live root.  This is a frozen
input-authority boundary, not a Character witness, B2, or B3A failure.

```text
REAL_ROOT_CONTACT = NONE_THIS_PHASE
REAL_ROOT_WRITE = NONE
REAL_P3_RESUME = NO
P4_EXECUTED = NO
P5_EXECUTED = NO
P6_EXECUTED = NO
P7_EXECUTED = NO
```
