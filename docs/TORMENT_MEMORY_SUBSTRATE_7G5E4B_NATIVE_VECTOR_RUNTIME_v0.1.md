# TORMENT Memory Substrate 7G5E4B — Native Vector Runtime

## Status and boundary

Starting revision: `4570d8197ac1418be46f10026c4ced3cf1c3751e`.

7G5E4B implements one substrate-owned, rebuildable process-local vector cache
for one explicit native memory lane. SQLite remains the only durable authority
for memory objects, current revisions, aliases, order, representations,
integrity, and reconciliation state. The matrix has no durable carrier and is
discarded on close or failed freshness validation.

`KERNEL_MATHEMATICS_CHANGED = NO`
`KERNEL_VECTORISATION_REPLACED = NO`
`KERNEL_DYNAMIC_BEHAVIOR_CHANGED = NO`
`FABRIC_PRODUCTION_WIRING_CHANGED = NO`
`NATIVE_ACTIVE = NO`
`DUAL_WRITE = NO`
`DUAL_READ = NO`
`CUTOVER_OPENED = NO`

There is no shared-domain admission, Fabric query selector, storage activation,
ANN/HNSW index, external vector database, migration, or writer wiring in this
slice. The component is directly instantiated only by qualification tests.

## Explicit lane identity

`NativeMemoryVectorRuntimeConfiguration` is immutable and binds:

```text
core database path + expected core UUID
workspace ID + scope kind + scope qualifier
legacy source namespace + identity namespace + semantic scope
representation class + generation + derivation contract
encoding + dtype + dimension
```

The scope is a validated `NativeMemoryRuntimeScope`. `PRIVATE_AGENT` uses
`agent_id` as its qualifier; `SHARED_DOMAIN` uses `domain_id`. The full lane
key contains every fact above. An EID is only an ordered row address *inside*
one such lane and is never globally meaningful.

Construction opens an existing core through the normal qualified SQLite
boundary, revalidates the STAGING/LEGACY_ACTIVE inert binding, and refuses an
embedder whose provider, model, declared dimension, or callable capability is
not the lane's exact caller-owned embedder. It neither creates an embedder nor
retains a caller's writer connection.

## Matrix and row-witness law

The native cache exactly follows the MemoryGraph fast-cache normalization law:

```text
v = np.asarray(value, dtype=np.float32).reshape(-1)
empty -> zeros(D, float32)
short -> right-pad; long -> truncate
n = float(np.linalg.norm(v) + 1e-12)
normalized = (v / n).astype(np.float32)
```

For a candidate rebuild, the runtime performs bounded bulk qualified reads:

1. validate all namespaced canonical EID aliases against the immutable
   `memory_runtime_enumeration_orders` carrier;
2. require each enumerated source to be a current `LEGACY_CORE_NODE` in the
   configuration's exact identity and semantic scope;
3. select only current
   `COMPAT_EMBEDDING/1/compat-embedding-v1/RAW_VECTOR/float32/D` rows with
   `READY`, `USABLE`, integrity `MATCH`, one expectation, durable bytes, and
   no non-usable reconciliation state;
4. validate exact byte length and finite raw float32 geometry; and
5. sort the qualified rows by ascending numeric EID, normalize, and
   `np.stack(...).astype(np.float32)`.

Runtime order proves complete source enumeration but does not define matrix
row order. Sources with no qualified current vector remain in the source
witness set and are omitted from the matrix, matching a legacy graph whose
memory has no loadable embedding.

Each matrix row stores:

```text
EID
native object ID
current object revision ID + ordinal
representation ID
selected integrity-measurement ID
SHA-256 raw-representation digest
```

The snapshot also retains every enumerated source witness, including the
runtime ordinal and a `None` representation witness where a current source is
not yet eligible. This makes a later READY publication observable without
making the absent row a vector result.

## Atomic freshness and invalidation

A candidate snapshot is fully assembled and re-witnessed before it replaces
`self._snapshot`. Any qualification, order, scope, byte, or concurrent-change
failure leaves no partial snapshot. A changed lane is made unavailable rather
than allowing an older vector to describe a new current revision.

The runtime has no writer integration. `invalidate(reason)` is explicitly
process-local: it marks only that instance/lane dirty and persists nothing.

Before every query, SQLite `PRAGMA data_version` is checked. If no external
write occurred, the resident matrix is used immediately. If it changed, the
runtime performs a fresh qualified source/vector witness pass and compares its
lane-local signature over exactly these memory-vector facts:

```text
EID alias/object/current revision/scope identity
runtime-order membership and ordinal
representation identity/source/lane/readiness/disposition/measurement result
integrity expectation identity and selected measurement
qualified raw-representation digest
```

An unchanged signature refreshes only the observed data version; it does not
rebuild the matrix. A noneligible representation moving between noneligible
states does not change geometry; if it becomes qualified it enters the observed
vector set and changes the signature. This keeps motif-only
object/relationship changes outside the memory-vector invalidation boundary. A
changed signature discards the old snapshot, rebuilds, and returns no cached
results if qualification cannot establish a new complete snapshot. Candidate
result projection performs a final current compatibility-view plus
qualified-representation witness check to refuse a write racing the query.

## Exact retrieval contract

`search_by_embedding()` preserves the cached `MemoryGraph` sequence:

```text
normalized float32 query
-> (float32 matrix @ query).astype(float32)
-> argsort(-scores) when N <= k
   otherwise argpartition(-scores, k - 1) followed by argsort of candidates
-> raw-score top-k candidates
-> min_score / canon / user / type filters
-> half-life decay
-> final sort by decayed score only
```

No UUID, SQLite rowid, or custom tie breaker is added. Empty, zero, short, and
long input vectors retain the legacy cached-normalization behavior. Qualified
stored vectors themselves refuse non-finite bytes; no query-side float64,
SciPy, SQL-cosine, or alternate epsilon path exists.

`search(query_text)` remains a distinct compatibility path. Blank text returns
no result. Nonblank text calls this lane's configured embedder exactly once,
then follows the same matrix path. It does not receive or substitute Fabric's
earlier domain-routing query embedding.

For selected candidates, the runtime obtains the current memory through
`NativeMemoryCompatibilityFacade`, not ad-hoc semantic payload joins. Results
keep the legacy-shaped fields (`eid`, raw/effective score, decay factor,
summary, type, strength, confidence, step, timestamp, and flexible payload)
without exposing native IDs as replacement legacy fields.

## Qualification evidence

`tests/test_substrate_native_memory_vector_runtime.py` proves:

- byte-identical normalized matrices, query bytes, float32 scores, candidate
  identities, filters, decay ordering, payload projection, and text/vector
  results against a real cached `MemoryGraph` corpus;
- zero, small nonzero, ordinary, padded, truncated, negative, tied, `N < k`,
  `N == k`, and `N > k` cache behavior;
- R1 READY inclusion; R2 current-without-READY exclusion; E2 inclusion;
  later integrity mismatch exclusion; and a successor with a newly qualified
  READY representation restoring the row;
- an invariant-failed rebuild clearing the active lane rather than publishing
  a partial matrix or re-serving its stale predecessor, followed by a clean
  rebuild once the invariant is available again;
- fresh-interpreter cold rebuild from only core path, explicit scope/lane, and
  caller-supplied embedder—without legacy JSONL/shards, MemoryGraph, or a
  migration snapshot;
- private and synthetic shared lanes with overlapping EID `0` but distinct
  matrix rows, results, and invalidation; and
- motif creation, motif state advance, and a membership-retiring native motif
  split changing no memory-vector witness and causing no matrix rebuild.

The pre-existing 7G5E4A cache characterization remains a regression companion:
the durable compatibility facade's float64 correctness scan is intentionally
not treated as a replacement for this exact live float32 cache.

## Bounded scale characterization

The opt-in scale test uses a structurally qualified, native SQLite test lane at
dimension 3. It does not time semantic writers: after one semantic admission,
the fixture bulk-shapes equivalent qualified rows with foreign-key enforcement
temporarily disabled, then restores enforcement and requires
`PRAGMA foreign_key_check` to be empty before any runtime reads. It separately
measures native SQLite-to-matrix cold reconstruction,
`MemoryGraph._rebuild_matrix()`, resident matrix bytes, and warm vector
retrieval. Warm native measurements include the normal `data_version` check
and current top-k projection, but not a whole-lane SQL scan.

| Memories | Matrix bytes | Native cold rebuild | Legacy matrix rebuild | Legacy warm search | Native warm search |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1,000 | 12,000 | 0.025690 s | 0.000316 s | 0.013788 ms | 1.113092 ms |
| 10,000 | 120,000 | 0.289768 s | 0.002990 s | 0.025360 ms | 4.663112 ms |
| 50,000 | 600,000 | 2.351768 s | 0.017046 s | 0.091416 ms | 43.372784 ms |

The acceptance condition is matching live algorithmic shape—one resident dense
float32 matrix, one normalized float32 query, vectorized matrix multiplication,
and NumPy top-k—not native microbenchmark superiority over a pre-existing
MemoryGraph matrix. The higher native warm measurements are explained by the
deliberate per-selected-result compatibility-view and qualified-representation
revalidation needed to refuse a durable write racing projection; no cached
matrix rebuild or whole-lane enumeration occurs on that path.

## Exclusions and next boundary

The runtime is a qualified primitive only. A later separately authorized slice
must decide whether to wire an explicit reader selector, how writers call the
invalidation hook after durable publication, and how a multi-lane shared-domain
admission descriptor is established. This slice does not change those owners.
