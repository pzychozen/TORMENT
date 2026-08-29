# TORMENT Memory Substrate — Phase 7F4 Integrated Migration Verification

## Scope

Phase 7F4 is a synthetic, offline verification package for the frozen legacy
migration boundaries already implemented through 7F3F. It adds no new semantic
family, live persistence wiring, cutover, production core, or dual-write path.

The coordinator verifies every manifest artifact before inventory or admission,
then invokes existing services in this explicit order:

1. identity and character definitions;
2. core objects;
3. core relationships;
4. core embedding representations;
5. motif objects and memberships;
6. deep-memory representations;
7. proposal effective state.

## Coverage matrix

| Family | Integrated disposition |
|---|---|
| `nodes.jsonl` | `ADMITTED_PRIMARY_STATE` |
| `edges.jsonl` | `ADMITTED_RELATIONSHIP` |
| embedding manifest/map/shard | `ADMITTED_DERIVATION`, intentionally non-READY |
| `identity.json` and `seed.json` | `ADMITTED_PRIMARY_STATE` |
| `character_state.json`, memory and motif events | `EVIDENCE_ONLY` |
| `motifs.json` and deep-memory captures | `ADMITTED_DERIVATION` |
| `proposals.jsonl` | `ADMITTED_PRIMARY_STATE` as `INTENT_PROPOSAL` |
| `proposal_events.jsonl` | `EVIDENCE_ONLY`; used only to derive frozen effective status |
| closure/conflict/ledger-shaped evidence | `EVIDENCE_ONLY` |
| old search/vector SQLite files | `ACCELERATION_ONLY` |
| unrecognized artifacts | `UNKNOWN` |

Captured evidence is not necessarily admitted, and admitted state is not live
runtime authority. Closure, conflict, authority, checkpoint, and collective
state admission remain unsupported.

## Representative synthetic fixture and exact result

The coherent fixture has 17 artifacts: three core nodes, one edge, one core
embedding chain, two identity definitions, one derived character-state file,
one motif and event file, one corroborated deep-memory capture, three proposals
with approved/rejected event evidence, one unknown artifact, one governance
ledger artifact, and one acceleration artifact.

Expected and verified native rows:

| Carrier | Count |
|---|---:|
| Objects | 9 |
| Relationships | 3 |
| Representations | 2 |
| Object aliases | 9 |
| Relationship aliases | 1 |
| Legacy admission records | 12 |
| Semantic transitions | 12 |

All 12 selected units are admitted. The two representations are
`UNKNOWN`/`RECONCILIATION_REQUIRED`; neither is falsely READY or
self-certified. No migration-created object has `ACTIVE_AUTHORIZATION`.

## Negative verification

The localized failure fixture proves that a dangling edge, invalid embedding
map, dangling motif member, uncorroborated deep-memory capture, and malformed
proposal event are individually contained. Good core source nodes remain
admitted; no placeholder relationship, partial motif, native representation,
or authority is fabricated.

Snapshot mutation after manifest creation fails before inventory and semantic
admission. Same-core repeat and moved-snapshot retries preserve durable results
without duplicate objects, revisions, aliases, admissions, transitions, or
operation results. A memory-optional identity-only rehearsal admits identity
and seed definitions with no core-memory dependency.

## Whole-core verification and limitations

The rehearsal performs bounded H1–H8 checks over the temporary SQLite core:
current pointers, typed effects, rejection exclusivity, any READY
representation, immutable aggregate trigger presence, reconciliation pointers,
typed legacy admission linkage, and exact operation outputs. Referential
closure is checked with direct joins and `PRAGMA foreign_key_check`.

The result is an integration proof for currently selected legacy families only;
it is not a claim that every historical TORMENT file is semantically migratable.
The next planned phase is 7G.
