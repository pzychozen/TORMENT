# 7G5E4E-A1 legacy query composite-identity repair

## Scope and outcome

A1 repairs the two A0 query-time identity leaks in the legacy Fabric query
path. It does not add a native query seam, selector, dual-read path, kernel
change, storage rewrite, Character change, or SRG change.

```text
PUBLIC_INGEST_BACKEND = LEGACY
PUBLIC_QUERY_BACKEND = LEGACY
NATIVE_ACTIVE = NO
DUAL_WRITE = NO
DUAL_READ = NO
PRODUCTION_SELECTOR_ADDED = NO
CUTOVER_OPENED = NO
```

## Continuity-anchor identity

### A0 witness

The old anchor top-k set was `set[int]`. A private qualifying `seed_canon`
with graph-local EID `1` made an unrelated shared non-canon
`identity_anchor` with graph-local EID `1` receive the full `0.12` anchor
bonus. The same problem applied to a bridge-peek shared hit when the source
domain was represented only by an equal EID comparison.

### A1 identity law

`torment_service.scoring.QueryMemoryIdentity` is the internal continuity
identity:

```text
workspace_id + scope + authoritative qualifier + eid

private = workspace_id + "private" + agent_id + eid
shared  = workspace_id + "shared" + domain_id + eid
```

`qualified_query_memory_identity()` validates the flattened legacy hit before
constructing this value. Missing workspace, scope, agent/domain qualifier, or
a negative/non-numeric EID fails closed. No bare-EID fallback remains.

`query()` constructs `anchor_full_boost_memory_ids` from the same qualified
source identity that `compute_continuity_bonuses()` later compares. `trace()`
uses the same helper and identity law to retain score/explanation parity.

Deep hits use `scope="deep"` and therefore do not infer a private identity for
the anchor comparison. The default native query profile remains deep-disabled;
A1 neither redesigns deep identity nor enables that profile.

Bridge-peek hits retain their flattened source `domain_id`; `bridge_domain`
remains routing metadata only. Shared identity comparison therefore uses the
destination graph's actual domain, never a bridge alias plus a bare EID.

## Motif geometry identity

### A0 witness

The old primary-domain centroid map was conceptually
`Dict[motif_id, centroid]`. If alpha and beta both contained `"same-id"`, the
later selected domain overwrote the first geometry. An alpha hit could thus be
scored against beta's motif centroid.

### A1 identity law

`_QueryMotifIdentity` is internal to Fabric query/trace geometry resolution:

```text
workspace_id + domain_id + motif_id
```

The selected-primary centroid map is now keyed by that complete value, in the
existing selected-domain and registry insertion order. Motif IDs remain stored
and exposed as their existing strings; they are not globally rewritten.

For a hit with stored motifs, A1 resolves each string only through validated
source `workspace_id`, `scope` (`private` or `shared`), and source
`domain_id`. An ordinary legacy private ingest already writes all three fields
from its chosen routing domain. Ordinary ingest currently stores no `motifs`
payload field, so it continues through the pre-existing no-stored-motif
fallback. If a historical stored private motif lacks a truthful source domain,
the resolver leaves it unresolved rather than choosing a selected domain,
nearest centroid, or same-string alias.

The fallback for hits without stored motifs is unchanged: it searches only the
selected primary centroid map, selects the best existing geometry with cosine
similarity at least `0.55`, and continues to expose the selected motif ID
string. Its internal winner is now a qualified motif identity.

Bridge-peek domains remain outside the primary centroid map. A bridge hit with
a stored motif cannot borrow a same-string primary centroid; absent source
geometry remains absent.

## Preserved contracts

```text
QUERY_SCORING_MATHEMATICS_CHANGED = NO
DOMAIN_ROUTING_MATH_CHANGED = NO
QUERY_EMBEDDER_CALL_BEHAVIOR_CHANGED = NO

PUBLIC_QUERY_RESULT_SCHEMA_CHANGED = NO
FINAL_QUERY_DEDUPE_ADDED = NO

CHARACTER_QUERY_BEHAVIOR_CHANGED = NO
SRG_QUERY_BEHAVIOR_CHANGED = NO

HISTORICAL_MEMORY_REWRITE = NO
HISTORICAL_MOTIF_REWRITE = NO

KERNEL_FILES_CHANGED = 0
KERNEL_MATHEMATICS_CHANGED = NO
KERNEL_GEOMETRY_CHANGED = NO
KERNEL_VECTORISATION_CHANGED = NO
KERNEL_RUNTIME_BEHAVIOR_CHANGED = NO
```

The repaired path changes only which existing, qualified identity can resolve
an equality or a stored motif centroid. It retains existing boost constants,
full/rest multipliers, cosine formula, `0.55` fallback threshold,
`score_hit`, reinforcement, SRG, MemoryPlan weights, final stable sort, and
domain-routing/embedder behavior.

## Characterization locks

`tests/test_7g5e4e_query_integration_preflight.py` now proves:

1. private/shared equal EIDs remain separate final rows;
2. a private qualifying anchor does not full-boost an equal-EID shared hit;
3. a private qualified identity retains its legitimate full anchor boost;
4. a bridge-peek shared equal-EID hit does not receive a private boost;
5. alpha and beta same-string motifs each use their own geometry;
6. a bridge hit cannot borrow a same-string primary centroid;
7. no-stored-motif fallback preserves aligned and below-threshold behavior;
8. requested-domain ordering and the five-call private/shared/bridge embedder
   law are unchanged.

## A0 reassessment

```text
QUERY_CONTINUITY_COMPOSITE_IDENTITY = QUALIFIED
QUERY_CONTINUITY_CROSS_SCOPE_EID_COLLISION = ELIMINATED
PRIVATE_CONTINUITY_ANCHOR_REGRESSION = PASS

QUERY_MOTIF_COMPOSITE_IDENTITY = QUALIFIED
QUERY_MOTIF_CROSS_DOMAIN_ID_COLLISION = ELIMINATED
BRIDGE_PEEK_MOTIF_CROSS_DOMAIN_FALSE_MATCH = NONE

BARE_EID_QUERY_IDENTITY_LEAK = CLOSED
BARE_MOTIF_ID_QUERY_IDENTITY_LEAK = CLOSED
CHARACTER_QUERY_SCOPE_AMBIGUITY = NO
KERNEL_CHANGE_REQUIRED = NO

E4E_QUERY_PREFLIGHT = READY
```

No new identity blocker emerged: ordinary private stored motif references have
an existing chosen-domain payload fact, while rows without a truthful stored
motif namespace fail closed rather than being assigned one.

## Remaining E4E implementation obligations

Readiness closes the two legacy reference-identity blockers. It does not mean
native retrieval is implemented or activated. A later, separately authorized
native query seam still needs a qualified private/shared read model, native
domain geometry and active-motif projection, and a scope-qualified
process-local SRG transient overlay for legacy parity. The existing
LLM-filtering exclusion diagnostic remains a bare EID report, but A1 leaves it
unchanged: it does not collapse results or participate in the repaired
continuity/motif identity decisions.
