# 7G5E4D-M2 Native Motif Merge Mutation

M2 qualifies one explicit STAGING-only native motif merge mutation.  It does
not select a storage backend, activate a runtime, change Fabric's public
legacy merge route, or move the retained JSON/JSONL workflow side store into
SQLite.

## Truth and workflow ownership

`NativeMotifService.merge_motifs` is the sole owner of the semantic mutation.
One `NATIVE_MOTIF_MERGE` transaction publishes both object successors, retires
every current dropped membership with an ordinary `RETIRED` successor, creates
only the missing survivor memberships, effects, operation outputs, and all
current pointers.  The dropped motif's `MOTIF_ID` alias remains historical
identity evidence; its current object revision is `RETIRED`, so runtime readers
exclude it from active geometry while direct historical resolution continues to
work.

The frozen legacy law is applied before publication:

- stronger motif survives (equal strengths preserve `a`);
- compatible centroids use the strength-weighted, unit-normalized centroid;
- strength is capped at `1.0`, contributing agents are sorted-unioned, and the
  survivor keeps identity, label, stability, and creation timestamp;
- current survivor membership is the exact EID-sorted union.  Existing survivor
  memberships remain; only dropped-only members receive new relationships.

The M1 `MotifSuggestionWorkflowStore` continues to own `motif_merges.json` and
`motif_events.jsonl`.  M2 adds only the external decision-state helpers it
needs.  Approval order is SQLite mutation, JSON status, then JSONL event.
Retries use the durable suggestion `created_ts` in both the operation key and
canonical native intent.  An already-approved status is not rewritten, and an
existing matching `MOTIF_MERGED` event is evidence that the JSONL append already
completed.  This covers the three intentionally tested lost-response windows:

1. SQLite committed before workflow status;
2. workflow status persisted before JSONL event;
3. JSONL event persisted before response.

No cross-store transaction, dual write, or shadow motif aggregate is added.

## Runtime reconciliation

`NativeMotifMergeRuntime` accepts only a claimed routing scope and uses its
source, semantic scope, motif identity/alias, membership identity, and
idempotency namespaces.  It rejects missing, retired, cross-scope, or
cross-domain motifs before mutation.  After a successful native merge it tells
the existing `NativeMotifProcessOrder` owner to remove the retired runtime ID;
an initialized process can therefore make the next attach without treating the
durable merge as an external catalog change.  A cold reader derives the same
live catalog directly from SQLite.

`NativePostWriteQualificationProfile.core_staging_with_motif_merge_maintenance()`
is the sole new explicit profile that marks both suggestion maintenance and
auto-merge as qualified.  M1 and baseline profiles remain unchanged.

## Qualification evidence

Focused tests cover:

- atomic rollback, exact idempotent retry, idempotency conflict, lost response,
  explicit effects/outputs/current pointers, and semantic-scope refusal;
- live-reader exclusion of the retired drop, historical alias resolution, and
  EID-sorted survivor membership projection;
- initialized and cold process-order recovery;
- manual decision recovery across all three cross-store interruption seams,
  JSONL de-duplication on retry, and legacy sequential auto-merge accounting;
- explicit M2 profile qualification while baseline and M1 remain frozen.

The work stops here.  It intentionally does not begin proposal orchestration,
E4E cutover, activation, selectors, dual writes, read migration, or kernel
work.
