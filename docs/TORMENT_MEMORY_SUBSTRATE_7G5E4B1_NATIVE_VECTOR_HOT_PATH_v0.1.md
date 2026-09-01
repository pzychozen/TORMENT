# TORMENT Memory Substrate 7G5E4B1 — Native Vector Hot Path

## Status and fixed boundary

Starting revision: `21d4989cb2a922d87191f096da7ac552d028b44e`.

7G5E4B1 closes the measured N+1 selected-result path beneath the inert native
vector runtime. It preserves the 7G5E4B matrix construction, float32
normalization, matmul, NumPy top-k, tie behavior, candidate-stage filters,
decay, and caller-owned text embedder invocation. It adds no Fabric selector,
shared admission, activation, durable cache state, schema migration, index, or
kernel change.

`NATIVE_ACTIVE = NO`
`DUAL_WRITE = NO`
`DUAL_READ = NO`
`CUTOVER_OPENED = NO`
`KERNEL_FILES_CHANGED = 0`
`FABRIC_PRODUCTION_WIRING_CHANGED = NO`

## Baseline archaeology

The original selected-row loop called, once per top-k result,
`NativeMemoryCompatibilityFacade.get_memory_by_eid()`,
`NativeCompatEmbeddingReader.read_current()`, and scope validation.

`EXPLAIN QUERY PLAN` showed that the facade's current object/revision lookup
was already an exact primary-key path. The reader's main query used the
representation source index, but its per-hit integrity cardinality subquery
performed `SCAN integrity_expectations`; its reconciliation subquery also
performed `SCAN reconciliation_cases`. Repeating that reader for every result
made fixed top-k validation grow with corpus size.

Baseline component characterization, in milliseconds per warm query, used the
existing dimension-3 qualified corpus. `Source` includes the complete
per-result currentness path; its children overlap by design.

| Rows | k | Matrix + top-k | Source | Compatibility | Embedding revalidation | Scope | Total |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1,000 | 1 | 0.01227 | 0.15862 | 0.04759 | 0.10050 | 0.00723 | 0.18941 |
| 1,000 | 8 | 0.01049 | 1.09808 | 0.28575 | 0.73487 | 0.05976 | 1.16131 |
| 1,000 | 32 | 0.01060 | 4.14116 | 1.05054 | 2.82089 | 0.20178 | 4.29535 |
| 10,000 | 1 | 0.03016 | 0.53850 | 0.04575 | 0.48220 | 0.00711 | 0.58383 |
| 10,000 | 8 | 0.02655 | 4.24219 | 0.30626 | 3.86465 | 0.05114 | 4.34072 |
| 10,000 | 32 | 0.02592 | 18.50547 | 1.76799 | 16.37023 | 0.24854 | 18.78668 |
| 50,000 | 1 | 0.08776 | 5.52516 | 0.12772 | 5.38169 | 0.00897 | 5.68692 |
| 50,000 | 8 | 0.10974 | 41.92196 | 0.96860 | 40.84300 | 0.06697 | 42.26519 |
| 50,000 | 32 | 0.12375 | 168.67195 | 4.10006 | 164.09205 | 0.29561 | 169.27657 |

## Bounded race-safe projection

`NativeMemoryCompatibilityFacade.get_memories_by_eids()` is the explicit
ordered batch compatibility boundary. It requires every supplied EID to map to
one current `LEGACY_CORE_NODE` revision in the caller's source namespace and
builds complete `LegacyMemoryView` values, including representation references,
in two bounded set reads. The vector runtime does not hand-build legacy payload
dictionaries.

`NativeCompatEmbeddingReader.validate_current_witnesses()` binds each selected
row's namespace EID, object/revision, representation ID, immutable expectation
ID, and selected measurement ID. It requires the same object revision to still
be current in the bound identity and semantic scope, `READY`, `USABLE`, and a
`MATCH` measurement. Reconciliation changes publish the representation's
current operational disposition, so `USABLE` is the direct current-state proof
that no non-usable reconciliation state remains.

The runtime begins one SQLite read transaction before that batched witness
read, then projects all selected compatibility views in that same transaction.
A writer committing before the read snapshot causes batch refusal; a writer
committing after it cannot produce a mixed old/new query result and is observed
by `data_version` on the next query.

Representation payloads are immutable after publication: schema triggers
reject both updates and deletes of `representation_payloads`; representation
and integrity-expectation fields are likewise immutable. Qualified publication
requires one pre-established expectation before payload publication. The hot
path therefore rechecks the immutable representation/expectation/measurement
identities and current state, rather than re-reading payload bytes and
rehashing them for every selected result.

For a warm query, post-selection execution is exactly three set-based `SELECT`
statements plus `BEGIN` and `COMMIT`:

1. batched row/current-representation/integrity witness;
2. batched compatibility current-memory projection; and
3. batched compatibility representation references.

The count is constant with corpus size and has no single-row facade or reader
call. It may return more rows or bind more parameters as `top_k` increases.

The final query plans for a 50k, top-32 read are requested-row-first:

- witness: materialized 32 requested rows followed by primary/index probes of
  alias `(namespace, kind, value)`, object revision, representation ID,
  expectation ID, measurement ID, and current state;
- compatibility memory view: alias primary key, object primary key, and object
  revision primary key; and
- representation references: 32 requested rows and the existing qualified
  representation source index.

Temporary ordering is limited to selected rows. No plan step scans a
corpus-sized selected-result table.

`INDEX_REQUIRED = NO`
`SCHEMA_VERSION_CHANGED = NO`

## Re-characterization

The original 7G5E4B top-8 warm baseline was 1.113092 ms at 1k, 4.663112 ms at
10k, and 43.372784 ms at 50k. The exact re-run after batching is below.

| Rows | Native cold rebuild | Legacy warm k=8 | Native warm k=8 |
| ---: | ---: | ---: | ---: |
| 1,000 | 0.025029 s | 0.016896 ms | 0.261616 ms |
| 10,000 | 0.284660 s | 0.030144 ms | 0.314072 ms |
| 50,000 | 2.385398 s | 0.075828 ms | 0.411536 ms |

Final component characterization, milliseconds per warm query:

| Rows | k | Matrix + top-k | Batch currentness | Batch projection | Native total |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1,000 | 1 | 0.01174 | 0.02523 | 0.03514 | 0.09788 |
| 1,000 | 8 | 0.01054 | 0.06765 | 0.15153 | 0.28275 |
| 1,000 | 32 | 0.01093 | 0.23108 | 0.50249 | 0.89777 |
| 10,000 | 1 | 0.02476 | 0.02689 | 0.03533 | 0.11014 |
| 10,000 | 8 | 0.02583 | 0.08255 | 0.16013 | 0.32950 |
| 10,000 | 32 | 0.02559 | 0.26805 | 0.59369 | 1.05110 |
| 50,000 | 1 | 0.08082 | 0.03418 | 0.03804 | 0.17419 |
| 50,000 | 8 | 0.09456 | 0.08524 | 0.14714 | 0.37421 |
| 50,000 | 32 | 0.08905 | 0.28787 | 0.54887 | 1.09726 |

For fixed `k`, selected-result validation is now bounded by selected rows and
does not materially grow from 1k to 50k. The 50k top-8 end-to-end warm cost
drops from 43.372784 ms to 0.411536 ms while preserving the frozen retrieval
law and race refusal.

## Qualification

The focused vector-runtime suite proves byte and result parity with cached
`MemoryGraph`, text-embedder call parity, stale R2 refusal, later integrity
mismatch/withdrawal refusal, newly READY E2 restoration, atomic failed rebuild
refusal, cold recovery, multi-lane isolation, and motif-only non-invalidation.
It additionally proves that the warm batch calls neither former single-row
lookup and emits exactly the five-statement read transaction above for
`top_k` 1, 8, and 32. A threaded writer commits R2 after the reader's batch
witness snapshot: that query returns only coherent R1 facts, and the next
query refuses the stale matrix row until a qualified successor exists.
