# TORMENT database convergence — context-bearing typed-source refusal qualification

Status: **QUALIFIED**

Date: 2026-09-05

Starting revision: `a0349e77094651edeed0063ac02988ef2c9b5fc0`
`origin/main`: `a0349e77094651edeed0063ac02988ef2c9b5fc0`

## Scope

This qualification changes only the diagnostic context emitted when an existing
typed-source regular-file check refuses. It does not inspect or contact the real
root, writer processes, or a production SQLite database.

`_regular_file` now retains its existing refusal prefix and reports the path
passed to it plus exactly one metadata-only shape:

- `SYMLINK` when `Path.is_symlink()` is true;
- `ABSENT` when the path is not present;
- `NON_FILE` when a present, non-symlink path is not a regular file.

The check neither resolves/follows symlinks nor reads, hashes, or recursively
inspects a path to produce that diagnostic. `_validate_regular_file` now retains
that cause beneath its existing label. `_file_observation` reaches the same
check for a present file path, and the existing JSON, hash, and NumPy-header
wrappers already allow `CorrectiveFreezePacketRefused` to propagate unchanged
before content processing; focused tests lock that behavior in.

## Qualification ledger

```text
CONTEXT_BEARING_TYPED_SOURCE_REFUSAL = QUALIFIED

FAILED_SOURCE_PATH_PRESERVED = YES
FAILED_SOURCE_SHAPE_PRESERVED = YES

VALID_REGULAR_FILE = PASS
ABSENT_PATH_DIAGNOSTIC = PASS
NON_FILE_PATH_DIAGNOSTIC = PASS
SYMLINK_PATH_DIAGNOSTIC = SKIPPED_HOST_CAPABILITY

_CAPTURE_PRESENT_CONTEXT = PASS
_VALIDATE_REGULAR_FILE_CONTEXT = PASS
_READ_JSON_CONTEXT = PASS
_HASH_FILE_CONTEXT = PASS
_FILE_OBSERVATION_CONTEXT = PASS
_NPY_HEADER_CONTEXT = PASS

SOURCE_GRAMMAR_CHANGED = NO
MIGRATION_SEMANTICS_CHANGED = NO
POSTURE_MODEL_CHANGED = NO
ROOT_EXCLUSIONS_CHANGED = NO

EMPTY_PRIVATE_LAW_CHANGED = NO
EMPTY_SHARED_WITH_MOTIF_LAW_CHANGED = NO
EMPTY_SHARED_WITHOUT_MOTIF_LAW_CHANGED = NO
DECLARED_EMPTY_SHARED_LAW_CHANGED = NO
REPRESENTATION_DISPOSITION_CHANGED = NO

NEW_HASH_LAW = NO
NEW_BYTE_IDENTICAL_LAW = NO
NEW_CANONICALIZATION_LAW = NO
PACKET_VERSION_CHANGED = NO
PACKET_SCHEMA_CHANGED = NO

REAL_ROOT_CONTACT = NONE
WRITER_CONTACT = NONE
SQLITE_PRODUCTION_WRITE = NONE
P1 = NOT_EXECUTED

READY_FOR_DIRECT_REAL_PREPARATION_ATTEMPT_4 = YES
```

## Synthetic evidence

All tests used disposable pytest roots outside the repository worktree.

```text
python -m py_compile torment_service/substrate/real_root_typed_evidence.py \
    tests/test_real_root_typed_evidence_adapter.py

pytest -q tests/test_real_root_typed_evidence_adapter.py
32 passed, 3 skipped

pytest -q tests/test_real_root_typed_evidence_adapter.py -k regular_file
2 passed, 1 skipped, 32 deselected
```

The skipped diagnostic case is the explicit Windows host-capability posture:
the test could not create a synthetic symlink. The production symlink refusal
remains mandatory and is not weakened. The full adapter suite and focused
diagnostic subset both exited successfully. During the full suite, Windows also
emitted intermittent access-violation tracebacks from unrelated synthetic
filesystem traversal even though pytest completed successfully; the focused
changed-case run was clean. Pytest additionally reported its pre-existing
repository cache access warning. No source or production path was used.

## Stop boundary

This qualification does not authorize a real-root retry. It created no staging
core or other durable production state. Attempt 4 requires fresh authorization.
