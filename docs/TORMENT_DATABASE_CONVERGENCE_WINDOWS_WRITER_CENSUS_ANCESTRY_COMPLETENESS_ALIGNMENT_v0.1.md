# TORMENT Database Convergence — Windows Writer Census Ancestry Completeness Alignment

**Date:** 2026-09-06
**Start revision:** `dc37830b6c249f4b3d35cb43a3e7e42d1ab81043` (`HEAD == origin/main`)

## Qualified rule

`census_direct_torment_tool_or_script` continues strict validation of every
individual record: typed record, positive PID, lawful non-negative parent PID,
non-self parent, non-empty image name, command-line text, and unique PID.

The census no longer requires every positive parent PID in the machine-wide
table to be present. Windows process churn can legitimately leave an
unrelated process with a parent that exited after the snapshot relationship was
formed. That readable process is classified from its own command line.

Only the exact supplied administration PID must resolve through every parent
to `parent_pid == 0`. A missing parent or cycle on that chain returns typed
`UNRESOLVED`. Only verified `cmd.exe`, `pwsh.exe`, and `powershell.exe` in
that chain retain `ADMINISTRATION_ANCESTOR_SHELL`; the exact current PID
retains `ADMINISTRATION_SELF`.

## Regression evidence

The affected synthetic suite proves:

- Attempt 10 administration ancestors containing admission terms remain
  `ABSENT` for direct-writer purposes.
- An unrelated `pid=5236, parent_pid=6860` record with missing PID 6860 no
  longer produces a global refusal.
- A matching writer with that same missing parent remains `RUNNING`.
- Missing/cyclic current-administration ancestry remains `UNRESOLVED`.
- Child, sibling, non-ancestor shell, and matching non-shell ancestor writer
  detection remain intact.

```text
python -m pytest tests/test_windows_real_admission_writer_census.py \
  tests/test_root_writer_freeze_evidence.py \
  tests/test_file_backed_real_admission_administration_runner.py \
  --basetemp _ptac2 -q

46 passed, 1 skipped
```

## Verdict

```text
WINDOWS_WRITER_CENSUS_ANCESTRY_COMPLETENESS_ALIGNMENT = QUALIFIED
GLOBAL_PARENT_COMPLETENESS_REQUIREMENT = REMOVED
CURRENT_ADMIN_ANCESTRY_COMPLETENESS = PRESERVED

UNRELATED_PARENT_CHURN = TOLERATED
UNRELATED_WRITER_DETECTION = PRESERVED

ADMINISTRATION_SELF = PRESERVED
ADMINISTRATION_ANCESTOR_SHELL = PRESERVED
WRITER_FREEZE_SEMANTICS_CHANGED = NO

PYTHON_NATIVE_COLLECTOR = NOT_PROMOTED

REAL_ROOT_CONTACT = NONE
SQLITE = NONE
P1 = NOT_EXECUTED

READY_FOR_WMIC_BACKED_ATTEMPT_13 = YES
```

## Stop boundary

This is a synthetic census qualification only. It does not perform Attempt 13
or authorize any real-root contact, source mutation, SQLite creation, P1, or
later phase.
