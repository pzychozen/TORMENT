# TORMENT Database Convergence — Direct Metadata-Less Workspace / Declared-Empty Domain Alignment

**Date:** 2026-09-05

## Result

`DIRECT_MISSING_WORKSPACE_META = QUALIFIED`

The direct reader now distinguishes a lawful workspace identity from a
workspace representation lock.  In direct preparation only, an absent
`workspace_meta.json` is captured as workspace-bound explicit absence evidence
with `METADATA_LESS_SOURCE_SHAPE`; it is not repaired, synthesized, or used to
infer a representation identity.  Corrective/packet capture retains its
historical strict required-file behavior.

The direct domain walk now treats `domains/<domain>/shared/`—not the domain
owner directory—as the shared materialization boundary.  A declared domain
directory without `shared/` is `DECLARED_EMPTY_SHARED`; a regular
`motifs.json` there is explicitly captured as present motif evidence while the
shared lane remains `NO_VECTOR` and unmaterialized.

## Synthetic qualification facts

The disposable six-workspace family proved:

| Fact | Result |
| --- | --- |
| Workspaces | 6: `sim-ws`, `ws1`, `ws2`, `ws3`, `ws4`, `ws5` |
| Materialized private scopes | 3 (`ws3/ws4/ws5` private `a1`) |
| Materialized shared scopes | 0 |
| Declared-empty shared scopes | 30 |
| Runtime scopes | 33 |
| `ws3/ws4/ws5` private `a1` | `UNKNOWN_IDENTITY` via existing Phase-9B metadata-less evidence |
| `research` motif-only domain | `DECLARED_EMPTY_SHARED`, `NO_VECTOR`, motif `PRESENT` |
| Other declared domains | `DECLARED_EMPTY_SHARED`, `NO_VECTOR`, motif `ABSENT` |

The manifest records every absent workspace metadata locator as:

```text
owner_class=WORKSPACE_IDENTITY_METADATA
owner_boundary=WORKSPACE(<workspace>)
canonical_locator=workspace_meta.json
semantic_role=WORKSPACE_META
presence_expectation=EXPECTED_ABSENT
scope_key=None
absence_reason=METADATA_LESS_SOURCE_SHAPE
```

Creating synthetic `workspace_meta.json` after capture makes manifest
verification refuse `expected-absent evidence was created`.

## Required verdicts

```text
DIRECT_MISSING_WORKSPACE_META = QUALIFIED
KNOWN_SIX_METADATALESS_WORKSPACES_REPRESENTABLE = YES
WORKSPACE_META_ABSENCE_EXPLICITLY_BOUND = YES
WORKSPACE_META_ABSENCE_DRIFT_REFUSES = YES
REPRESENTATION_IDENTITY_INFERRED_FROM_ABSENCE = NO
UNQUALIFIED_MEMORY_GRAPH_WITHOUT_LOCK_STILL_REFUSES = YES
WS3_WS4_WS5_UNKNOWN_IDENTITY_PATH_PRESERVED = YES

DECLARED_EMPTY_DOMAIN_DIRECTORY_WITHOUT_SHARED = QUALIFIED
MOTIF_ONLY_DOMAIN_DIRECTORY = DECLARED_EMPTY_SHARED
DECLARED_EMPTY_WITH_MOTIF_B3 = 0
DECLARED_EMPTY_WITH_MOTIF_B4C_PATH = PRESERVED
DECLARED_EMPTY_WITHOUT_MOTIF_B3 = 0
DECLARED_EMPTY_WITHOUT_MOTIF_B4 = 0
SHARED_MATERIALIZATION_BOUNDARY = domains/<domain>/shared

SOURCE_GRAMMAR_BROADENED_BEYOND_FROZEN_LAW = NO
LEGACY_SOURCE_REPAIR_REQUIRED = NO
REAL_ROOT_CONTACT = NONE
WRITER_CONTACT = NONE
SQLITE_PRODUCTION_WRITE = NONE
P1 = NOT_EXECUTED
READY_FOR_DIRECT_REAL_PREPARATION_ATTEMPT_5 = YES
```

## Qualification runs

```text
python -m py_compile (changed modules and adapter test) = PASS
tests/test_real_root_typed_evidence_adapter.py = 37 passed, 3 skipped

tests/test_substrate_root_admission_description.py
tests/test_substrate_root_normalization.py
tests/test_substrate_migration_runtime_zero_member_motif_projection.py
tests/test_substrate_generalized_runtime_readiness.py
tests/test_post_i4_generalized_root_blocker5_binding.py
= 51 passed
```

The Windows host intermittently emitted access-violation diagnostics during
pytest filesystem activity, but every listed qualification command exited
successfully.  The initial default temporary directory was inaccessible and
long repository-local temporary paths exceeded Windows path length limits;
the passing runs used short disposable synthetic temp roots.  No real-root
path, writer surface, service, or production SQLite path was contacted.

## Stop boundary

This is a reader qualification only.  It does not perform Attempt 5, create a
native core, persist a root-admission envelope, enter cutover, normalize any
source, execute P5/P6/P7, or restart a service.
