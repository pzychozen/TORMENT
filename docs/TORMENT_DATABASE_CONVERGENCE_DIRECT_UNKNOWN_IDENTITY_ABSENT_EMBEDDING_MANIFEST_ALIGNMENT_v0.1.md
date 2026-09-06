# TORMENT Database Convergence — Direct Unknown-Identity Absent Embedding-Manifest Alignment

**Date:** 2026-09-06
**Required start revision:** `3bb79db9bdf2ec3dab2526b21efd0cbaad0a7fdc` (`HEAD == origin/main`)

## Result

Attempt 8 established that the frozen direct source has no
`embeddings/manifest.json` in three otherwise qualified metadata-less private
scopes. Direct preparation now captures that absence as typed evidence only
when all of the following facts hold:

- direct-admission preparation is the caller;
- the workspace has the existing metadata-less source shape
  (`workspace_meta.json` is expected absent);
- the private scope is exactly `ws3|PRIVATE|a1`, `ws4|PRIVATE|a1`, or
  `ws5|PRIVATE|a1`; and
- the existing disposition is `UNKNOWN_IDENTITY`.

For each such scope, `embeddings/manifest.json` is recorded as:

```text
owner_class=EMBEDDING_MANIFEST
canonical_locator=embeddings/manifest.json
semantic_role=EMBEDDING_MANIFEST
presence_expectation=EXPECTED_ABSENT
absence_reason=METADATA_LESS_SOURCE_SHAPE
```

This is an evidence-only source-shape alignment. It does not create a
manifest, inspect vector storage to establish an identity, rewrite source, or
run an embedding operation. The historical corrective-freeze packet capture
continues to require the manifest as a regular non-symlink file.

## Fail-closed boundary

The exception is neither a general missing-manifest rule nor a replacement
storage format. An ordinary materialized memory graph without a manifest still
refuses. A manifest at one of the three expected-absent paths—even malformed—
also refuses during direct preparation. Manifest verification refuses if such
a path appears later; expected-absent symlinks are treated as drift too.

The synthetic six-workspace census remains explicit and unchanged:

| Fact | Value |
| --- | --- |
| Workspaces | 6: `sim-ws`, `ws1`, `ws2`, `ws3`, `ws4`, `ws5` |
| Materialized private scopes | 3: `ws3/ws4/ws5` private `a1` |
| Materialized shared scopes | 0 |
| Declared-empty shared scopes | 30 |
| Runtime scopes | 33 |

The metadata-less per-EID source still retains provider and model identity as
`None` and representation identity as `UNKNOWN`. Existing downstream
qualification maps that state to `REEMBED_REQUIRED` and supplies its canonical
source input; it does not relabel, infer from NPY/dtype/content/path/stamps, or
execute re-embedding.

## Synthetic qualification runs

```text
python -m py_compile (changed modules and adapter test) = PASS
tests/test_real_root_typed_evidence_adapter.py = 41 passed, 3 skipped

tests/test_substrate_root_admission_description.py
tests/test_substrate_metadata_less_per_eid_legacy_source.py
= 20 passed
```

All tests used repository-local disposable pytest roots. The host emitted its
usual inaccessible `.pytest_cache` warning, but every listed command exited
successfully. No real root, writer/listener surface, SQLite database, service,
or admission attempt was contacted.

## Required verdicts

```text
DIRECT_UNKNOWN_IDENTITY_ABSENT_EMBEDDING_MANIFEST = QUALIFIED
QUALIFIED_SCOPES = ws3|PRIVATE|a1,ws4|PRIVATE|a1,ws5|PRIVATE|a1
EMBEDDING_MANIFEST_EXPECTATION = EXPECTED_ABSENT
REPRESENTATION_DISPOSITION = UNKNOWN_IDENTITY
REEMBED_SOURCE = CANONICAL_SOURCE
REPRESENTATION_INFERENCE_FROM_STORAGE = FORBIDDEN
ORDINARY_MISSING_MANIFEST = REFUSE
EXPECTED_ABSENCE_DRIFT = REFUSE
REAL_ROOT_CONTACT = NONE
SQLITE_PRODUCTION_WRITE = NONE
P1 = NOT_EXECUTED
READY_FOR_DIRECT_REAL_PREPARATION_ATTEMPT_9 = YES
```

## Stop boundary

This qualification does not perform Attempt 9. It does not contact a real
root, census a production writer or listener, create or modify a manifest or
workspace metadata, mutate legacy source, open production SQLite, create
staging state, run P1/P2, normalize, execute embeddings, or change authority,
migration, writer-freeze, or database semantics.
