# TORMENT Memory Substrate — Phase 7G5A3C1S Schema Evolution / Governance / Provenance v0.1

## Status

**COMPLETE.** This narrow substrate slice supersedes the schema-capability
finding in the A3C1 blocker note. It does not implement the A3C1 Fabric
translation boundary.

Starting authority: `5aaade93e1ac6bfe689895fc4b05c6262f86b1a9`.

## Version decision

The historical schema remains **v1.0**. The current schema is **v1.1**.

```text
v1.0 exact core
  -- explicit upgrade only -->
v1.1 exact core
```

This is a minor evolution because the addition is a strictly additive immutable
child table. It changes neither the interpretation nor the validity of an
existing v1.0 object revision. A pure schema upgrade does not backfill
governance values or infer historical meaning from `governance_state`.

`SCHEMA_V1_DDL` is retained as the real historical bootstrap. Normal
`create_schema()` creates a new v1.1 core; `create_schema_v1()` exists only to
make historical-v1 recognition and evolution qualification explicit. Both
versions are structurally recognized by `open_schema()`. Opening never mutates
a core. APIs that require the new carrier use `require_current_schema()` and
refuse v1.0 until the named upgrade has completed.

## Revision-bound governance carrier

`object_revision_governance` has one immutable primary-key row at most for an
exact object revision:

```text
(object_id, object_revision_id, object_revision_ordinal)
  -> object_revisions(object_id, object_revision_id, revision_ordinal)
```

Its five required, independently queryable `INTEGER NOT NULL CHECK (... IN
(0,1))` facts are:

- `protected`
- `non_shareable`
- `collective_export_blocked`
- `collective_reingest_blocked`
- `decay_accelerated`

The all-false vector is an explicit known value, never an interpretation of an
absent row. An absent child remains distinguishable for old or otherwise
unqualified revisions. For a future ordinary compatibility-memory write, the
write contract—not a global schema trigger—will require exactly one row for its
published revision. This avoids imposing invented facts on historical and
other object families.

`object_revisions.governance_state` remains the existing coarse structural
fact. It does not encode this vector. With no frozen mapping between them, the
coarse state and the behavioral vector are orthogonal; no disagreement rule is
invented. Likewise, `lifecycle_state="PROTECTED"` and `protected=1` are
distinct facts, and ordinary memory retains
`authority_category="NOT_APPLICABLE"`.

`NativeObjectRevisionGovernanceService` reads the exact child without parsing a
payload. Its current-object convenience method follows the committed current
pointer; absence is returned as `None`, not as a fabricated all-false vector.

## Explicit upgrade protocol

`upgrade_schema_v1_to_v1_1()` is the only evolution path. It requires a
qualified connection and an exact validated v1.0 source, then performs:

```text
BEGIN IMMEDIATE
  create object_revision_governance
  create its immutable UPDATE/DELETE refusal triggers
  validate the new carrier shape and immutability triggers
  record one SCHEMA_UPGRADE maintenance event
  record TMS_SCHEMA_V1_TO_V1_1_GOVERNANCE in the migration ledger
  update core metadata from 1.0 to 1.1
  validate the complete v1.1 schema
COMMIT
```

Any exception rolls back all of these changes. Metadata is deliberately last
among durable upgrade state. An already-current valid v1.1 core returns its
metadata without creating another maintenance or ledger record. A malformed
v1, unsupported newer version, wrong schema identifier, or hybrid structure
fails closed.

The upgrade leaves `core_role`, `deployment_state`, and activation state
unchanged. It creates no governance rows for pre-existing revisions and makes
no deployment or authority claim. There is no automatic upgrade on open and no
generic migration framework.

## Closed-child provenance qualification

The qualification primitive demonstrates a single memory semantic operation:

```text
BEGIN IMMEDIATE
  insert immutable provenance row
  create memory R1 referencing that exact provenance_id
  publish the memory object transition, effect, and output
  insert the exact R1 governance child
  validate revision closure
COMMIT
```

The durable result is the memory revision. The existing operation output can
recover its exact R1 after a lost Python response; R1's `provenance_id` then
resolves the same immutable provenance row. Repeating the same idempotent
operation recovers the same object, revision, transition, operation, and
provenance IDs. A changed provenance intent conflicts, and a forced failure
after the provenance insert publishes neither provenance nor memory residue.

H2 and H8 remain satisfied by the memory revision's existing typed effect and
output. The provenance row is the immutable referenced structural child that
closes that revision; it is not a separately published carrier.

```text
PROVENANCE_ROW_PRESENT != INDEPENDENT_PROVENANCE_TRANSITION
PROVENANCE_CLOSED_CHILD_MODEL = PASS
STANDALONE_PROVENANCE_PUBLICATION_REQUIRED = NO
```

No provenance output kind, provenance effect family, provenance payload shadow,
or provenance object kind is introduced.

## Structural validation and qualification

The v1.1 validator requires the exact additional table, columns, affinities,
STRICT mode, composite primary key, composite foreign key, five boolean checks,
and immutable child triggers. It also rejects unexpected tables, indexes, or
triggers for either declared schema version and verifies the migration ledger's
maintenance evidence.

Focused qualification proves fresh v1.0 creation and explicit upgrade, fresh
v1.1 bootstrap, malformed/newer/wrong-ID refusal, forced-upgrade rollback,
governance boolean and FK refusal, duplicate refusal, immutability, R1/R2
historical versus current reads, lifecycle/governance separation, and
closed-child provenance success/retry/conflict/rollback.

## Deferrals

This phase deliberately defers A3C1 Fabric structural translation (including
scope, `ProvenanceV1`, governance projection, and `signals.links`
classification), A3C2 source-plus-motif composition, A3C3 reinforcement,
A3D Fabric routing, A4 Character work, native split/merge, real runtime
binding, dual read/write, native activation, and cutover.

```text
FABRIC_NATIVE_ROUTING = NO
DOMAIN_ROUTER_NATIVE_ROUTING = NO
CHARACTER_NATIVE_ROUTING = NO
MEMORY_MOTIF_COMPOUND_RUNTIME_WRITE = NO
REINFORCEMENT_NATIVE_ROUTING = NO
RUNTIME_MOTIF_ID_ALLOCATION = NO
NATIVE_ACTIVE = NO
DUAL_WRITE = NO
DUAL_READ = NO
CUTOVER = NO
AUTHORITY_EXPANSION = NO
```
