"""Pure Windows process-census support for real-admission administration.

This module has no process-enumeration or process-control capability.  A
caller injects one complete Windows process table and explicitly identifies
the administration process it is running in.  The helper applies the existing
direct-writer command-line predicate while preventing that observation from
mistaking its own process, or its command-shell ancestors, for an independent
writer.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import PureWindowsPath
import re
from typing import Sequence

from .writer_freeze_evidence import (
    RootWriterClass,
    WriterObservationResult,
    WriterProcessObservation,
)


WINDOWS_INJECTED_PROCESS_CENSUS_MECHANISM = "WINDOWS_INJECTED_PROCESS_CENSUS_V2"

_DIRECT_TORMENT_PATTERN = re.compile(r"torment", re.IGNORECASE)
_DIRECT_WRITER_ACTION_PATTERN = re.compile(
    r"(write|writer|ingest|migration|normalize|bootstrap|admission|repair|clone)",
    re.IGNORECASE,
)
_ADMINISTRATION_ANCESTOR_SHELLS = frozenset({"cmd.exe", "pwsh.exe", "powershell.exe"})


class WindowsProcessCensusClassification(str, Enum):
    """The direct-writer disposition of one injected process record."""

    ADMINISTRATION_SELF = "ADMINISTRATION_SELF"
    ADMINISTRATION_ANCESTOR_SHELL = "ADMINISTRATION_ANCESTOR_SHELL"
    DIRECT_TORMENT_TOOL_OR_SCRIPT = "DIRECT_TORMENT_TOOL_OR_SCRIPT"
    NOT_DIRECT_TORMENT_TOOL_OR_SCRIPT = "NOT_DIRECT_TORMENT_TOOL_OR_SCRIPT"


@dataclass(frozen=True)
class WindowsProcessRecord:
    """The minimum injected Windows process facts needed for this census.

    Validation occurs in :func:`census_direct_torment_tool_or_script`, rather
    than here, so malformed injected facts can fail closed as an ``UNRESOLVED``
    observation instead of escaping as a constructor error.
    """

    pid: int
    parent_pid: int
    name: str
    command_line: str


@dataclass(frozen=True)
class WindowsProcessClassification:
    """One process record with its resolved direct-writer disposition."""

    record: WindowsProcessRecord
    classification: WindowsProcessCensusClassification


@dataclass(frozen=True)
class WindowsDirectWriterCensusResult:
    """A deterministic direct-writer census result with fail-closed state."""

    current_administration_pid: int
    administration_ancestry_pids: tuple[int, ...]
    process_classifications: tuple[WindowsProcessClassification, ...]
    direct_writer_observation: WriterProcessObservation
    unresolved_reason: str | None

    @property
    def resolved(self) -> bool:
        return self.direct_writer_observation.result is not WriterObservationResult.UNRESOLVED

    @property
    def refused(self) -> bool:
        return self.direct_writer_observation.result in {
            WriterObservationResult.RUNNING,
            WriterObservationResult.UNRESOLVED,
        }

    @property
    def direct_writer_pids(self) -> tuple[int, ...]:
        return tuple(
            item.record.pid
            for item in self.process_classifications
            if item.classification
            is WindowsProcessCensusClassification.DIRECT_TORMENT_TOOL_OR_SCRIPT
        )


def census_direct_torment_tool_or_script(
    *,
    records: Sequence[WindowsProcessRecord],
    current_administration_pid: int,
) -> WindowsDirectWriterCensusResult:
    """Classify the existing direct-writer rule with bounded ancestry context.

    Every record is validated independently. Only the supplied current
    administration PID must have a complete, acyclic parent chain through
    ``parent_pid == 0``. Unrelated parent churn does not hide a readable
    process's own direct-writer classification. The exact current PID and
    command-shell records in its verified parent chain are the only exclusions
    from the direct-writer predicate.
    """

    table, invalid_reason = _validated_process_table(records, current_administration_pid)
    if invalid_reason is not None:
        return _unresolved_result(current_administration_pid, invalid_reason)
    assert table is not None  # Narrowed by the fail-closed branch above.

    ancestry, ancestry_reason = _resolve_administration_ancestry(table, current_administration_pid)
    if ancestry_reason is not None:
        return _unresolved_result(current_administration_pid, ancestry_reason)
    assert ancestry is not None  # Narrowed by the fail-closed branch above.

    ancestry_pids = set(ancestry)
    classifications = tuple(
        WindowsProcessClassification(
            record=record,
            classification=_classify_process(
                record,
                current_administration_pid=current_administration_pid,
                administration_ancestry_pids=ancestry_pids,
            ),
        )
        for record in sorted(table.values(), key=lambda item: item.pid)
    )
    direct_writer_present = any(
        item.classification
        is WindowsProcessCensusClassification.DIRECT_TORMENT_TOOL_OR_SCRIPT
        for item in classifications
    )
    return WindowsDirectWriterCensusResult(
        current_administration_pid=current_administration_pid,
        administration_ancestry_pids=ancestry,
        process_classifications=classifications,
        direct_writer_observation=WriterProcessObservation(
            RootWriterClass.DIRECT_TORMENT_TOOL_OR_SCRIPT,
            WINDOWS_INJECTED_PROCESS_CENSUS_MECHANISM,
            WriterObservationResult.RUNNING if direct_writer_present else WriterObservationResult.ABSENT,
        ),
        unresolved_reason=None,
    )


def _validated_process_table(
    records: Sequence[WindowsProcessRecord],
    current_administration_pid: int,
) -> tuple[dict[int, WindowsProcessRecord] | None, str | None]:
    if (
        not isinstance(current_administration_pid, int)
        or isinstance(current_administration_pid, bool)
        or current_administration_pid <= 0
    ):
        return None, "INVALID_CURRENT_ADMINISTRATION_PID"
    if isinstance(records, (str, bytes)) or not isinstance(records, Sequence):
        return None, "PROCESS_RECORDS_MUST_BE_A_SEQUENCE"

    table: dict[int, WindowsProcessRecord] = {}
    for record in records:
        if not isinstance(record, WindowsProcessRecord):
            return None, "INVALID_PROCESS_RECORD_TYPE"
        if not isinstance(record.pid, int) or isinstance(record.pid, bool) or record.pid <= 0:
            return None, "INVALID_PROCESS_PID"
        if (
            not isinstance(record.parent_pid, int)
            or isinstance(record.parent_pid, bool)
            or record.parent_pid < 0
            or record.parent_pid == record.pid
        ):
            return None, f"INVALID_PARENT_RELATION: pid={record.pid}"
        if not isinstance(record.name, str) or not record.name.strip():
            return None, f"INVALID_PROCESS_NAME: pid={record.pid}"
        if not isinstance(record.command_line, str):
            return None, f"INVALID_PROCESS_COMMAND_LINE: pid={record.pid}"
        if record.pid in table:
            return None, f"DUPLICATE_PROCESS_PID: pid={record.pid}"
        table[record.pid] = record

    if current_administration_pid not in table:
        return None, f"CURRENT_ADMINISTRATION_PID_NOT_FOUND: pid={current_administration_pid}"
    return table, None


def _resolve_administration_ancestry(
    table: dict[int, WindowsProcessRecord],
    current_administration_pid: int,
) -> tuple[tuple[int, ...] | None, str | None]:
    ancestry: list[int] = []
    seen: set[int] = set()
    pid = current_administration_pid
    for _ in range(len(table) + 1):
        if pid == 0:
            return tuple(ancestry), None
        record = table.get(pid)
        if record is None:
            return None, f"MISSING_ANCESTRY_PROCESS: pid={pid}"
        if pid in seen:
            return None, "ADMINISTRATION_ANCESTRY_CYCLE"
        seen.add(pid)
        ancestry.append(pid)
        pid = record.parent_pid
    return None, "ADMINISTRATION_ANCESTRY_EXCEEDED_BOUND"


def _classify_process(
    record: WindowsProcessRecord,
    *,
    current_administration_pid: int,
    administration_ancestry_pids: set[int],
) -> WindowsProcessCensusClassification:
    if record.pid == current_administration_pid:
        return WindowsProcessCensusClassification.ADMINISTRATION_SELF
    if record.pid in administration_ancestry_pids and _is_administration_ancestor_shell(record.name):
        return WindowsProcessCensusClassification.ADMINISTRATION_ANCESTOR_SHELL
    if _matches_existing_direct_writer_rule(record.command_line):
        return WindowsProcessCensusClassification.DIRECT_TORMENT_TOOL_OR_SCRIPT
    return WindowsProcessCensusClassification.NOT_DIRECT_TORMENT_TOOL_OR_SCRIPT


def _is_administration_ancestor_shell(name: str) -> bool:
    return PureWindowsPath(name.strip()).name.casefold() in _ADMINISTRATION_ANCESTOR_SHELLS


def _matches_existing_direct_writer_rule(command_line: str) -> bool:
    return bool(
        _DIRECT_TORMENT_PATTERN.search(command_line)
        and _DIRECT_WRITER_ACTION_PATTERN.search(command_line)
    )


def _unresolved_result(
    current_administration_pid: int,
    reason: str,
) -> WindowsDirectWriterCensusResult:
    return WindowsDirectWriterCensusResult(
        current_administration_pid=current_administration_pid,
        administration_ancestry_pids=(),
        process_classifications=(),
        direct_writer_observation=WriterProcessObservation(
            RootWriterClass.DIRECT_TORMENT_TOOL_OR_SCRIPT,
            WINDOWS_INJECTED_PROCESS_CENSUS_MECHANISM,
            WriterObservationResult.UNRESOLVED,
        ),
        unresolved_reason=reason,
    )


__all__ = [
    "WINDOWS_INJECTED_PROCESS_CENSUS_MECHANISM",
    "WindowsDirectWriterCensusResult",
    "WindowsProcessCensusClassification",
    "WindowsProcessClassification",
    "WindowsProcessRecord",
    "census_direct_torment_tool_or_script",
]
