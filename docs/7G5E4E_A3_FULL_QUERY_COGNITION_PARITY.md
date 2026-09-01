# 7G5E4E-A3: Qualification-only full query cognition parity

## Scope and production boundary

A3 qualifies SQLite-backed memory reads beneath the existing `TormentFabric`
query orchestration.  It does not select native storage for any public route.
`TormentFabric.query()` constructs `LegacyQualifiedQueryReadModel` unless the
private test-only `_query_with_read_model()` entrypoint supplies an injected
model.  There is no `/agent/query` or `/retrieve` selector, environment
toggle, dual-read, dual-write, shadow-read, or public native activation.

Kernel files and kernel mathematics are unchanged.

## One orchestration law

The public query method retains its established pipeline:

1. Fabric routing embedding and workspace dimension check.
2. Domain routing, requested-domain reordering, and MemoryPlan budgets.
3. Private, primary shared, and BridgeRegistry-directed peek lane retrieval.
4. Existing candidate concatenation, exclusion, motif alignment, conflict,
   continuity, reinforcement, SRG, provenance, lane weight, rank, and filter
   logic.
5. Existing active-motif, bridge, role, embed, Character, collective, explain,
   and continuity-debug result assembly.

Only the memory-read facts are injected.  The legacy and native models both
provide lane searches, shared-domain geometry, and active motifs.  Native lane
search remains `NativeMemoryVectorRuntime.search`; Fabric retains the first
routing embed call.  BridgeRegistry, ConflictRegistry, CharacterStore, and
governance remain Fabric/external owners.

The internal compatibility carrier holds the A1 qualified hit identity until
scoring completes, then is removed before the existing public result surface.
Native motif memberships are projected from current qualified relationships;
legacy payload memberships are otherwise left untouched.

## Native-qualified profile

The A3 profile has deep/compression retrieval disabled.  Injected native query
raises `ValueError` if deep retrieval is enabled, rather than mixing native
core candidates with legacy deep candidates.  Public legacy deep behavior is
unchanged.

Native SRG uses `NativeSRGProcessState` and the existing
`NativeSRGTransientRuntime`.  The exact scoped current object/revision witness
is re-read before each effective-state read or overlay replacement.  An SRG
overlay is used as the next breathing input and mirrors the current
compatibility payload view during that query.  It does not write a SQLite
memory successor.

## Differential fixture and coverage

`tests/test_7g5e4e_query_cognition_parity.py` runs the same Fabric query law
over the A2 legacy and native readers.  The SQLite fixture contains private,
research, engineering, and archive lanes; overlapping graph-local EIDs;
research/engineering `same-id` motifs with different geometry; motif-less
records; reinforcement/decay; a distinct archive bridge-peek destination; and
current-ready vector representations.

The qualification tests compare whole result dictionaries for:

- automatic and requested routing, stable equal-score domain order, unknown
  domain failure, blank text, and zero/explicit MemoryPlan budgets;
- private/shared/bridge candidates, lane call aggregation (one routing plus
  private, two primary shared, and bridge-peek lane calls), score/order,
  motif fallback, active motifs, explain, and continuity debug;
- scope-qualified conflict joins across colliding EIDs, collective provenance
  discount, and post-top-k non-shareable filtering without refill;
- self-thread/thread-window continuity, reinforcement, Character context, and
  Character weighted diagnostics without changing `final_score`;
- native SRG score multipliers and cumulative process-local breathing, while
  asserting the native current revision is unchanged; and
- close/reopen of the native read model and vector runtimes with identical
  qualified query output.

## Evidence

Native qualification environment:

```text
conda environment: torment-substrate
SQLite: 3.53.4
tests/test_7g5e4e_native_query_read_model.py
tests/test_7g5e4e_query_cognition_parity.py
15 passed
```

Public legacy regression environment:

```text
conda environment: torment
tests/test_7g5e4e_query_integration_preflight.py
tests/test_query_explain_shape.py
tests/test_conflict_origin_scope.py
tests/test_continuity_centralization.py
32 passed
```

Verdict:

```text
E4E_A3_FULL_QUERY_COGNITION = QUALIFIED
PUBLIC_QUERY_BACKEND = LEGACY
FABRIC_PUBLIC_NATIVE_QUERY_WIRED = NO
NATIVE_ACTIVE = NO
DUAL_READ = NO
DUAL_WRITE = NO
PRODUCTION_SELECTOR_ADDED = NO
DEFAULT_A3_DEEP_PROFILE = DISABLED
ENABLED_DEEP_NATIVE_QUERY = REFUSED
KERNEL_FILES_CHANGED = 0
```

Remaining E4E work remains a separately authorized production-convergence
decision; A3 opens no runtime cutover path.
