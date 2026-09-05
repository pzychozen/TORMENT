# TORMENT Memory Substrate — Held-Freeze Alternate-Root Static Reconciliation v0.1

## Status

```text
STOPPED_V1_REFUSAL = VALID
ROOT_PREDECESSOR_EQUALITY_FROM_V1 = PASS
HELD_FREEZE_RELEASED = NO
CORRECTIVE_PACKET_ALTERNATE_ROOT_TYPING = QUALIFIED
REAL_ROOT_CONTACT = NONE
WRITER_CONTACT = NONE
```

The stopped V1 corrective capture correctly refused an unclassified durable
top-level root artifact. This static-only reconciliation identifies that
artifact category from the already committed source doctrine; it does not
revisit the production root or retry capture.

```text
ALTERNATE_SELECTED_ROOT_CLASSIFICATION = FROZEN_EXISTING_LAW
LIVED_USE = PREEXISTING_EXCLUDED_ALTERNATE_SELECTED_ROOT
LIVED_USE_SOURCE_ADMISSION = NO
LIVED_USE_CONTENT_CAPTURE = NO
LIVED_USE_RECURSIVE_HASHING = NO
LIVED_USE_EXTERNAL_OWNER_CLASS = NO
LIVED_USE_ROOT_SCOPE_KEY = NONE
ADAPTER_MODEL_GAP = YES
```

`data/workspaces/**` remains the selected production source. `data/nodes.jsonl`
and `data/emb_1.npy` remain excluded top-level legacy **files**. `data/lived_use/**`
is a selected alternate root, not a child of the selected source and not a
`RootScopeKey` memory or admission input. Its contents were not interpreted.

## Narrow contract repair

Packet version is now `3`. It adds distinct frozen types:

- `ExcludedAlternateRootExpectation`
- `ExcludedAlternateRootObservation`
- `ExcludedAlternateRootRole.ALTERNATE_SELECTED_ROOT`
- adapter configuration `ExcludedAlternateRootLocator`

An alternate-root observation serializes only its top-level locator, frozen
role, `DIRECTORY` kind, and `PRESENT` state. It deliberately contains no child
path, hash, count, snapshot, content-derived identity, manifest entry, or
runtime/source-scope plan input.

The existing excluded-file types and their regular-file SHA-256 requirements
are unchanged. An alternate root cannot use those types. The source manifest
semantics are unchanged and do not absorb `lived_use` or any descendant.

```text
NEW_SEMANTIC_OWNER_DISCOVERED = NO
ALTERNATE_ROOT_CONTENT_ADMITTED = NO
ALTERNATE_ROOT_CONTENT_HASHED = NO
ROOT_EVIDENCE_MANIFEST_SEMANTICS_CHANGED = NO
EXCLUDED_LEGACY_FILE_SEMANTICS_CHANGED = NO
LIVED_USE_CONTENT_HASH_ADDED_TO_PREDECESSOR = NO
```

The root validator remains strict. It permits only `workspaces`, configured
excluded top-level legacy files, and configured alternate-root directories.
Missing, regular-file, symlink/reparse, nested, duplicate, overlapping, or
unexpected root declarations refuse. Alternate-root observation reads no child
directory and performs no recursive enumeration.

## Synthetic qualification

The disposable production-shaped fixture now includes:

```text
root/lived_use/arbitrary_nested_basin/embedding_manifest.json  (malformed)
root/lived_use/arbitrary_nested_basin/malformed.npy            (malformed)
```

Successful qualification proves these irrelevant nested files are neither
parsed, classified, hashed by the adapter, added to the source manifest, nor
admitted as scope evidence. It also proves packet serialization and strict
offline reload preserve the alternate-root classification after deleting the
fixture source.

The suite covers declared/undeclared alternate roots, unexpected fourth root,
regular-file and nested locator refusal, duplicate declaration refusal,
symlink refusal where the Windows host permits symlink creation, packet digest
closure, source-tree byte identity, and the existing UNKNOWN_IDENTITY,
EMPTY_PRIVATE, DECLARED_EMPTY_SHARED, motif-presence, and excluded-file paths.

```cmd
call C:\Users\Notandi\miniconda3\condabin\conda.bat activate torment
python -m pytest tests\test_real_root_typed_evidence_adapter.py tests\test_held_freeze_corrective_evidence_capture.py -q --basetemp _pytest_tmp_alternate_root_static_r2 -p no:cacheprovider
```

```text
TEST_RESULT = 32 passed, 1 skipped
```

The skipped case is only the platform-dependent synthetic symlink setup;
Windows environments where a directory symlink can be created execute the
refusal assertion.

The final directly affected regression run additionally included the
writer-freeze evidence unit suite:

```cmd
call C:\Users\Notandi\miniconda3\condabin\conda.bat activate torment
python -m pytest tests\test_real_root_typed_evidence_adapter.py tests\test_held_freeze_corrective_evidence_capture.py tests\test_root_writer_freeze_evidence.py -q --basetemp _pytest_tmp_alternate_root_static_final -p no:cacheprovider
```

```text
FINAL_TEST_RESULT = 49 passed, 2 skipped
```

## Non-results and next authority

```text
PRODUCTION_WRITER_CONTACT = NONE
PROVIDER_CONTACT = NONE
MODEL_LOADING = NONE
BRAINVISION_OPENED = NO
SECOND_COGNITIVE_FUNCTION_INSPECTED = NO
```

This repair changes the future corrective-packet contract. It does not release
the held freeze or reuse the prior V1 real-capture authorization. A fresh,
explicit real-capture authorization is required before any real-root contact.
