from __future__ import annotations

import pytest

from torment_service.substrate.windows_real_admission_writer_census import (
    WINDOWS_INJECTED_PROCESS_CENSUS_MECHANISM,
    WindowsProcessCensusClassification,
    WindowsProcessRecord,
    census_direct_torment_tool_or_script,
)
from torment_service.substrate.writer_freeze_evidence import (
    RootWriterClass,
    WriterObservationResult,
)


_CURRENT_ADMINISTRATION_PID = 300


def _record(pid: int, parent_pid: int, name: str, command_line: str) -> WindowsProcessRecord:
    return WindowsProcessRecord(
        pid=pid,
        parent_pid=parent_pid,
        name=name,
        command_line=command_line,
    )


def _attempt_10_process_table(*extra: WindowsProcessRecord) -> tuple[WindowsProcessRecord, ...]:
    return (
        _record(
            100,
            0,
            "cmd.exe",
            "cmd.exe /d /c torment admission bootstrap attempt-10",
        ),
        _record(
            200,
            100,
            "pwsh.exe",
            "pwsh.exe -Command direct-real-admission-p1-attempt-10 bootstrap",
        ),
        _record(
            _CURRENT_ADMINISTRATION_PID,
            200,
            "python.exe",
            "python.exe -m torment_service.substrate.detached_real_admission_child_entrypoint "
            "--execute-external-script attempt10_driver.py",
        ),
        *extra,
    )


def _classifications_by_pid(result: object) -> dict[int, WindowsProcessCensusClassification]:
    return {
        item.record.pid: item.classification
        for item in result.process_classifications  # type: ignore[attr-defined]
    }


def test_attempt_10_administration_ancestry_is_not_mistaken_for_a_direct_writer() -> None:
    result = census_direct_torment_tool_or_script(
        records=_attempt_10_process_table(),
        current_administration_pid=_CURRENT_ADMINISTRATION_PID,
    )

    classifications = _classifications_by_pid(result)
    assert result.resolved is True
    assert result.refused is False
    assert result.administration_ancestry_pids == (300, 200, 100)
    assert classifications[100] is WindowsProcessCensusClassification.ADMINISTRATION_ANCESTOR_SHELL
    assert classifications[200] is WindowsProcessCensusClassification.ADMINISTRATION_ANCESTOR_SHELL
    assert classifications[300] is WindowsProcessCensusClassification.ADMINISTRATION_SELF
    assert result.direct_writer_pids == ()
    assert result.direct_writer_observation.writer_class is RootWriterClass.DIRECT_TORMENT_TOOL_OR_SCRIPT
    assert result.direct_writer_observation.observation_mechanism == WINDOWS_INJECTED_PROCESS_CENSUS_MECHANISM
    assert result.direct_writer_observation.result is WriterObservationResult.ABSENT


@pytest.mark.parametrize(
    "writer",
    (
        _record(400, 0, "pwsh.exe", "pwsh.exe -File C:\\ops\\torment-write.ps1"),
        _record(400, 0, "python.exe", "python.exe -m torment_service.migration.writer"),
        _record(400, _CURRENT_ADMINISTRATION_PID, "python.exe", "python.exe torment ingest writer"),
        _record(400, 200, "python.exe", "python.exe -m torment_service admission"),
    ),
    ids=("unrelated_shell", "unrelated_python", "writer_child", "writer_sibling"),
)
def test_non_ancestor_or_descendant_writers_remain_detected(writer: WindowsProcessRecord) -> None:
    result = census_direct_torment_tool_or_script(
        records=_attempt_10_process_table(writer),
        current_administration_pid=_CURRENT_ADMINISTRATION_PID,
    )

    classifications = _classifications_by_pid(result)
    assert result.resolved is True
    assert result.refused is True
    assert result.direct_writer_pids == (400,)
    assert classifications[400] is WindowsProcessCensusClassification.DIRECT_TORMENT_TOOL_OR_SCRIPT
    assert result.direct_writer_observation.result is WriterObservationResult.RUNNING


def test_non_shell_administration_ancestor_remains_subject_to_existing_direct_writer_rule() -> None:
    records = (
        _record(50, 0, "python.exe", "python.exe -m torment_service admission"),
        _record(100, 50, "cmd.exe", "cmd.exe /d /c torment bootstrap attempt-10"),
        _record(200, 100, "pwsh.exe", "pwsh.exe -Command attempt-10"),
        _record(
            _CURRENT_ADMINISTRATION_PID,
            200,
            "python.exe",
            "python.exe -m torment_service.substrate.detached_real_admission_child_entrypoint",
        ),
    )

    result = census_direct_torment_tool_or_script(
        records=records,
        current_administration_pid=_CURRENT_ADMINISTRATION_PID,
    )

    classifications = _classifications_by_pid(result)
    assert classifications[50] is WindowsProcessCensusClassification.DIRECT_TORMENT_TOOL_OR_SCRIPT
    assert result.direct_writer_pids == (50,)
    assert result.direct_writer_observation.result is WriterObservationResult.RUNNING


@pytest.mark.parametrize(
    "records,current_pid,reason",
    (
        (
            (
                _record(100, 0, "cmd.exe", "cmd.exe"),
                _record(100, 0, "pwsh.exe", "pwsh.exe"),
            ),
            100,
            "DUPLICATE_PROCESS_PID: pid=100",
        ),
        (
            (
                _record(100, 200, "cmd.exe", "cmd.exe"),
                _record(200, 100, "pwsh.exe", "pwsh.exe"),
            ),
            100,
            "PROCESS_TREE_CYCLE",
        ),
        (
            (_record(100, 999, "cmd.exe", "cmd.exe"),),
            100,
            "MISSING_PARENT_PROCESS: pid=100; parent_pid=999",
        ),
        (
            (_record(100, 0, "cmd.exe", "cmd.exe"),),
            999,
            "CURRENT_ADMINISTRATION_PID_NOT_FOUND: pid=999",
        ),
    ),
    ids=("duplicate_pid", "cycle", "missing_parent", "missing_current_pid"),
)
def test_malformed_process_trees_fail_closed_as_unresolved(
    records: tuple[WindowsProcessRecord, ...],
    current_pid: int,
    reason: str,
) -> None:
    result = census_direct_torment_tool_or_script(
        records=records,
        current_administration_pid=current_pid,
    )

    assert result.resolved is False
    assert result.refused is True
    assert result.administration_ancestry_pids == ()
    assert result.process_classifications == ()
    assert result.unresolved_reason == reason
    assert result.direct_writer_observation.writer_class is RootWriterClass.DIRECT_TORMENT_TOOL_OR_SCRIPT
    assert result.direct_writer_observation.result is WriterObservationResult.UNRESOLVED
