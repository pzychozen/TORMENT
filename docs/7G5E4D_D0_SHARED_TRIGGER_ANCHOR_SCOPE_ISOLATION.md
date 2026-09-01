# 7G5E4D-D0: shared-trigger identity-anchor scope isolation

## Decision

D0 repairs a pre-existing legacy identity leak in derived identity-anchor
work. The derived-memory context now carries the original stored-memory
`trigger_scope`. Identity-anchor emission and identity-anchor refinement are
applicable only when that scope is `private`.

```text
private trigger -> existing identity-anchor emission and refinement
shared trigger  -> anchor emission: no-op; anchor refinement: no-op
```

Mood drift is deliberately unchanged. M1 motif entropy/suggestion maintenance
is also deliberately unchanged.

## The collision that was removed

Before D0, a shared ingest could use a shared-domain motif whose `members`
contained integer EIDs such as `[1, 2]`. The legacy anchor writer then tested
those values for presence in the private agent graph and read private affect,
summary, and seed data for equal integers. The result could incorrectly claim
private rows 1 and 2 as the source members of the shared motif.

Bare EID equality is not an identity relation. EIDs are local to their
private-agent or shared-domain namespace. No authoritative shared-to-private
identity mapping exists, and D0 does not invent one by numeric collision,
summary text, embedding similarity, proposal ancestry, or any other heuristic.

The repair occurs at the derived semantic-operation boundary, before either
anchor operation can inspect private graph rows, side stores, embeddings, or
native SQLite state. The post-write coordinator still executes the same
ordered slots:

```text
M1 maintenance
anchor emission call       -> governed shared no-op
anchor refinement call     -> governed shared no-op
mood drift                 -> existing behavior
later consumers
```

## Scope and history

`trigger_scope` is propagated from the actual `FabricPostWriteContext.scope`;
it is never inferred from a destination runtime or motif ID. The accepted
Fabric vocabulary is `private` and `shared`.

This is prospective-only producer repair. D0 does not delete, rewrite,
retire, or infer provenance for historical identity anchors. It does not
change anchor authority: legitimate private-trigger anchors remain automatic,
derived private memory with `canon = false`.

## Native parity

The native derived runtime applies the identical no-op law before its
qualified-scope checks or any SQLite/side-store activity. This preserves the
substrate invariant that a legacy EID is meaningful only with its namespace;
it does not introduce a cross-scope native binding, selector, dual write/read,
or activation path.

## D0 exclusions

D0 does not qualify shared M1 materialization, shared native derived-memory
materialization, shared mood drift, direct shared ingest, vector freshness, or
the next D1 work. Those remain separate work after this repaired legacy
producer boundary is established.
