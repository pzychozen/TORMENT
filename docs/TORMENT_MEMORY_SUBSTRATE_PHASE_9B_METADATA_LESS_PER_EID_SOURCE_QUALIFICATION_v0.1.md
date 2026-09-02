# TORMENT Memory Substrate Phase 9B — Metadata-Less Per-EID Source Qualification v0.1

## Status

```text
PHASE_9B_METADATA_LESS_SOURCE = PASS
PER_EID_SOURCE_EVIDENCE = PASS
CANONICAL_TEXT_CONTINUITY = PASS
LEGACY_VECTOR_RETENTION = PASS
B3B_INTEGRATION_SEAM = PASS

FORMAT_QUALIFIED_SYNTHETICALLY = YES
REAL_SOURCE_ELIGIBILITY_NOT_YET_ADMINISTERED = YES
```

Phase 9B qualifies bounded migration-import evidence for one metadata-less
private legacy source shape. It does not admit memory, create a native core,
construct a runtime, derive a target vector, or activate public authority.

## Qualified source contract

The adapter accepts exactly one private `RootScopeKey` and these explicit,
owner-bounded witnesses:

```text
nodes.jsonl                         REQUIRED / PRESENT
edges.jsonl                         OPTIONAL / PRESENT OR EXPLICITLY ABSENT
emb_<nonnegative-EID>.npy           REQUIRED / PRESENT
```

The representation witness is accepted only under the new closed Phase 9A
owner class:

```text
METADATA_LESS_PER_EID_LEGACY_REPRESENTATION
```

It is private-scope-only and has the existing `LEGACY_REPRESENTATION` role.
The generic legacy-artifact owner cannot enter this adapter. Filename forms,
paths, source scope, and declared EID must agree exactly; nested forms,
traversal, absolute escape, shared boundaries, mismatched EIDs, and unknown
extensions refuse.

The adapter records immutable historical evidence only:

```text
canonical owner-relative locator
RootScopeKey
legacy EID
nodes/graph evidence identity
legacy representation evidence identity
byte length and SHA-256
array dtype, one-dimensional shape, and observed dimension
legacy source namespace and target identity namespace
```

It does not record or infer provider, model, generation, or semantic
representation class. The frozen outcome is:

```text
REPRESENTATION_IDENTITY = UNKNOWN
UNKNOWN_PROVIDER_REMAINS_UNKNOWN = YES
UNKNOWN_MODEL_REMAINS_UNKNOWN = YES
DIMENSION_DOES_NOT_ESTABLISH_REPRESENTATION_IDENTITY = YES
UNKNOWN_LEGACY_VECTOR_CAN_BECOME_TARGET_BY_RELABEL = NO
```

## Canonical text and B3B boundary

The declared `nodes.jsonl` is parsed only through its named evidence locator.
The source EID must map to exactly one well-formed record with a `payload`
mapping. Canonical embedding input is selected by the existing frozen
`summary`-then-`text` contract; no second text-selection rule was introduced.

The resulting B3B hand-off contains canonical text, its digest, the complete
scope/namespace identity, retained legacy evidence, and:

```text
LEGACY_VECTOR_STRATEGY = REEMBED_REQUIRED
```

It contains no legacy vector bytes. Existing B3B target derivation semantics
remain the sole future re-embedding implementation; no B3B/B3A code was
rewritten and no target model was loaded for this phase.

Retry comparison binds full source semantics under an idempotency namespace
and key. An identical source repeats its identity; a semantic source change
under the same idempotency identity raises a conflict. Recheck reads only the
three declared locators and refuses node drift, vector drift, or vector
deletion. An extra `emb_<other-EID>.npy` neither substitutes for nor changes
the declared witness.

## Qualification administration

Port 8787 was empty before every Phase 9B test execution and after the final
run. No service, MCP process, provider, or API was started.

The selected offline regression inventory was statically checked for
localhost/8787, HTTP clients, service startup, URL configuration, and default
production-root construction:

- `tests/test_substrate_metadata_less_per_eid_legacy_source.py`
- `tests/test_substrate_root_admission_description.py`
- `tests/test_substrate_migration_inventory.py`
- `tests/test_substrate_migration_runtime_readiness.py`
- `tests/test_substrate_canonical_intent.py`
- `tests/test_substrate_ids.py`
- `tests/test_memory_graph_path_hardening.py`

All fixture storage is `tmp_path`, a temporary test connection, or a temporary
directory.

```text
SELECTED_NETWORK_CAPABLE_TESTS = 0
NETWORK = NONE
LIVE_SERVICE = NONE
REAL_ROOT_CONTACT = NONE
```

The focused Phase 9B suite passed `9` tests. The full selected offline set
passed `62` tests in `2.66s`.

## Safety and convergence accounting

```text
REAL_ROOT_CONTACT = NO
REAL_ws3_ws4_ws5_ACCESSED = NO
REAL_MEMORY_MODEL_CONTACT = 0
REAL_REEMBED_OPERATIONS = 0

SELECTOR_CREATED = NO
NATIVE_CORE_CREATED = NO
REAL_ADMISSION_RUN = NO
CUTOVER_RUN = NO
KERNEL_FILES_CHANGED = 0

BRAINVISION_FILES_READ = 0
BRAINVISION_FILES_TOUCHED = 0
BRAINVISION_DATA_TOUCHED = 0
BRAINVISION_EVIDENCE_TOUCHED = 0

NEW_PARALLEL_PUBLIC_RUNTIME = NO
NEW_TRANSITIONAL_DUPLICATION =
    metadata-less per-EID legacy import/source adapter only
EVENTUAL_SURVIVOR =
    generalized bounded legacy import support feeding one B3B implementation
PERMANENT_MIGRATION_IMPORT_SUPPORT = POSSIBLE
```

The real `ws3`, `ws4`, and `ws5` layouts remain untouched. Their actual
operator eligibility, root-wide target representation normalization, motif
qualification, admission, and activation remain later separately authorized
work.
