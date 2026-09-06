# TORMENT Database Convergence — Windows Writer Census Administration-Ancestor Alignment

**Date:** 2026-09-06
**Start revision:** `798ee2eda8a1ce7592d8b86fdc7f9fa12d29545f` (`HEAD == origin/main`)

## Scope

This qualification closes Attempt 10's process-census false positive using
only injected, synthetic Windows process records. It makes no live process,
listener, root, SQLite, or service observation.

The reusable helper is
`torment_service.substrate.windows_real_admission_writer_census`. A caller
supplies a complete process table and its exact current administration PID.
The table contains PID, parent PID, executable name, and command line.

## Qualified observation rule

The existing broad direct-writer command-line predicate remains unchanged:
`torment` plus one of `write`, `writer`, `ingest`, `migration`, `normalize`,
`bootstrap`, `admission`, `repair`, or `clone`.

The helper resolves the supplied process's parent chain deterministically,
with a bound of the injected table size. It returns the existing typed
`WriterProcessObservation` for
`DIRECT_TORMENT_TOOL_OR_SCRIPT` in every result.

Only these records are disambiguated before that existing predicate is
considered:

- The exact supplied current administration PID is classified
  `ADMINISTRATION_SELF`.
- A record is classified `ADMINISTRATION_ANCESTOR_SHELL` only when it is in
  that resolved parent chain and its executable is `cmd.exe`, `pwsh.exe`, or
  `powershell.exe`.

All other records, including non-ancestor shells, non-shell ancestors,
administration children, siblings, and unrelated Python processes, remain
subject to the unchanged direct-writer rule. Duplicate PIDs, absent or
invalid parents, cycles, malformed records, and an absent/ambiguous current
PID fail closed as a typed `UNRESOLVED` direct-writer observation.

## Synthetic qualification evidence

`tests/test_windows_real_admission_writer_census.py` injects the Attempt 10
shape:

```text
cmd.exe ancestor  ->  pwsh.exe ancestor  ->  current administration python
```

All three command lines contain the prior broad administration terms. The
two shell records resolve to `ADMINISTRATION_ANCESTOR_SHELL`; the current
Python record resolves to `ADMINISTRATION_SELF`; the resulting direct-writer
observation is `ABSENT`.

The same suite proves that a non-ancestor `pwsh.exe`, unrelated Python,
writer child, and writer sibling still yield `RUNNING`. It also proves a
matching non-shell ancestor remains detected and that malformed ancestry data
returns `UNRESOLVED`. `tests/test_root_writer_freeze_evidence.py` confirms
the existing typed writer-freeze evidence contract remains green.

## Test result

```text
python -m pytest tests/test_windows_real_admission_writer_census.py \
  tests/test_root_writer_freeze_evidence.py \
  tests/test_held_freeze_corrective_evidence_capture.py \
  tests/test_file_backed_real_admission_administration_runner.py \
  --basetemp _ptw -q

63 passed, 1 skipped
```

## Verdict

```text
WINDOWS_WRITER_CENSUS_ADMINISTRATION_ANCESTOR_ALIGNMENT = QUALIFIED
ATTEMPT_10_FALSE_POSITIVE_CLASS = CLOSED

ADMINISTRATION_SELF_EXCLUSION = QUALIFIED
ADMINISTRATION_ANCESTOR_SHELL_EXCLUSION = QUALIFIED
NON_ANCESTOR_PROCESS_DETECTION = PRESERVED
WRITER_CHILD_DETECTION = PRESERVED

REST_WRITER_SEMANTICS_CHANGED = NO
MCP_WRITER_SEMANTICS_CHANGED = NO
FABRIC_HOST_SEMANTICS_CHANGED = NO
WRITER_FREEZE_SEMANTICS_CHANGED = NO

REAL_ROOT_CONTACT = NONE
SQLITE_PRODUCTION_WRITE = NONE
P1 = NOT_EXECUTED

READY_FOR_DIRECT_REAL_PREPARATION_ATTEMPT_11 = YES
```

## Stop boundary

This qualification does not authorize Attempt 11 or any real root census. A
future authorized administration must separately supply its process records,
its current PID, and its own result directory.
