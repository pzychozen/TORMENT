from __future__ import annotations

import json
from pathlib import Path

import pytest

import torment_service.substrate.file_backed_real_admission_administration_runner as administration
from torment_service.substrate.file_backed_real_admission_administration_runner import (
    FileBackedRealAdmissionAdministrationRefused,
    FileBackedRealAdmissionAdministrationRunner,
    FileBackedRealAdmissionAdministrationWriteError,
    RealAdmissionAdministrationState,
)


def _paths(tmp_path: Path) -> tuple[Path, Path, Path]:
    data_root = tmp_path / "synthetic-data"
    legacy_source = data_root / "workspaces" / "ws-one" / "source.txt"
    legacy_source.parent.mkdir(parents=True)
    legacy_source.write_bytes(b"synthetic legacy source")
    result_directory = tmp_path / "administration-results" / "operation-one"
    return data_root, legacy_source, result_directory


def _runner(tmp_path: Path, *, append_events: bool = True) -> tuple[FileBackedRealAdmissionAdministrationRunner, Path]:
    data_root, legacy_source, result_directory = _paths(tmp_path)
    return FileBackedRealAdmissionAdministrationRunner(
        data_root=data_root,
        result_directory=result_directory,
        operation_id="synthetic-real-admission-qualification",
        append_events=append_events,
    ), legacy_source


def _checkpoint(runner: FileBackedRealAdmissionAdministrationRunner, *states: RealAdmissionAdministrationState) -> None:
    for state in states:
        runner.checkpoint(state, detail={"synthetic_state": state.value})


def test_rejects_a_result_directory_inside_the_supplied_data_root(tmp_path: Path) -> None:
    data_root, _legacy_source, _result_directory = _paths(tmp_path)

    with pytest.raises(FileBackedRealAdmissionAdministrationRefused, match="outside data_root"):
        FileBackedRealAdmissionAdministrationRunner(
            data_root=data_root,
            result_directory=data_root / "administration-results" / "forbidden",
            operation_id="synthetic-inside-data-root",
        )


def test_atomic_current_state_and_optional_append_only_events_are_external(tmp_path: Path) -> None:
    runner, legacy_source = _runner(tmp_path)
    before = legacy_source.read_bytes()
    _checkpoint(
        runner,
        RealAdmissionAdministrationState.RUNNER_STARTED,
        RealAdmissionAdministrationState.PRECHECK_STARTED,
        RealAdmissionAdministrationState.PRECHECK_PASS,
        RealAdmissionAdministrationState.CAPTURE_STARTED,
        RealAdmissionAdministrationState.CAPTURE_RETURNED,
        RealAdmissionAdministrationState.DIRECT_PREPARATION_PASS,
        RealAdmissionAdministrationState.P1_NOT_AUTHORIZED,
        RealAdmissionAdministrationState.FINAL_STOP,
    )

    current = json.loads(runner.state_path.read_text(encoding="utf-8"))
    assert current["state"] == "FINAL_STOP"
    assert current["sequence"] == 8
    assert runner.current_checkpoint is not None
    assert runner.current_checkpoint.state is RealAdmissionAdministrationState.FINAL_STOP
    assert not list(runner.result_directory.glob("*.tmp"))
    events = [json.loads(line) for line in runner.events_path.read_text(encoding="utf-8").splitlines()]
    assert [event["state"] for event in events] == [
        "RUNNER_STARTED", "PRECHECK_STARTED", "PRECHECK_PASS", "CAPTURE_STARTED",
        "CAPTURE_RETURNED", "DIRECT_PREPARATION_PASS", "P1_NOT_AUTHORIZED", "FINAL_STOP",
    ]
    assert legacy_source.read_bytes() == before
    assert runner.result_directory not in legacy_source.parents


@pytest.mark.parametrize(
    "states",
    (
        (
            RealAdmissionAdministrationState.RUNNER_STARTED,
            RealAdmissionAdministrationState.PRECHECK_STARTED,
            RealAdmissionAdministrationState.PRECHECK_REFUSED,
            RealAdmissionAdministrationState.FINAL_STOP,
        ),
        (
            RealAdmissionAdministrationState.RUNNER_STARTED,
            RealAdmissionAdministrationState.PRECHECK_STARTED,
            RealAdmissionAdministrationState.PRECHECK_PASS,
            RealAdmissionAdministrationState.CAPTURE_STARTED,
            RealAdmissionAdministrationState.CAPTURE_REFUSED,
            RealAdmissionAdministrationState.FINAL_STOP,
        ),
        (
            RealAdmissionAdministrationState.RUNNER_STARTED,
            RealAdmissionAdministrationState.PRECHECK_STARTED,
            RealAdmissionAdministrationState.PRECHECK_PASS,
            RealAdmissionAdministrationState.CAPTURE_STARTED,
            RealAdmissionAdministrationState.CAPTURE_EXCEPTION,
            RealAdmissionAdministrationState.FINAL_STOP,
        ),
        (
            RealAdmissionAdministrationState.RUNNER_STARTED,
            RealAdmissionAdministrationState.PRECHECK_STARTED,
            RealAdmissionAdministrationState.PRECHECK_PASS,
            RealAdmissionAdministrationState.CAPTURE_STARTED,
            RealAdmissionAdministrationState.CAPTURE_RETURNED,
            RealAdmissionAdministrationState.DIRECT_PREPARATION_REFUSED,
            RealAdmissionAdministrationState.FINAL_STOP,
        ),
        (
            RealAdmissionAdministrationState.RUNNER_STARTED,
            RealAdmissionAdministrationState.PRECHECK_STARTED,
            RealAdmissionAdministrationState.PRECHECK_PASS,
            RealAdmissionAdministrationState.CAPTURE_STARTED,
            RealAdmissionAdministrationState.CAPTURE_RETURNED,
            RealAdmissionAdministrationState.DIRECT_PREPARATION_PASS,
            RealAdmissionAdministrationState.P1_READY,
            RealAdmissionAdministrationState.P1_STARTED,
            RealAdmissionAdministrationState.P1_PASS,
            RealAdmissionAdministrationState.FINAL_VERIFICATION_PASS,
            RealAdmissionAdministrationState.FINAL_STOP,
        ),
        (
            RealAdmissionAdministrationState.RUNNER_STARTED,
            RealAdmissionAdministrationState.PRECHECK_STARTED,
            RealAdmissionAdministrationState.PRECHECK_PASS,
            RealAdmissionAdministrationState.CAPTURE_STARTED,
            RealAdmissionAdministrationState.CAPTURE_RETURNED,
            RealAdmissionAdministrationState.DIRECT_PREPARATION_PASS,
            RealAdmissionAdministrationState.P1_READY,
            RealAdmissionAdministrationState.P1_STARTED,
            RealAdmissionAdministrationState.P1_FAILED_AFTER_DURABLE_STATE,
            RealAdmissionAdministrationState.FINAL_STOP,
        ),
    ),
)
def test_every_required_nonexception_outcome_has_a_durable_legal_path(
    tmp_path: Path,
    states: tuple[RealAdmissionAdministrationState, ...],
) -> None:
    data_root, _legacy_source, result_directory = _paths(tmp_path)
    result_directory = result_directory.parent / f"operation-{states[-2].value.lower()}"
    runner = FileBackedRealAdmissionAdministrationRunner(
        data_root=data_root,
        result_directory=result_directory,
        operation_id=f"synthetic-{states[-2].value.lower()}",
    )
    _checkpoint(runner, *states)

    assert json.loads(runner.state_path.read_text(encoding="utf-8"))["state"] == states[-1].value


def test_administration_exception_is_durable_without_an_event_log(tmp_path: Path) -> None:
    runner, _legacy_source = _runner(tmp_path, append_events=False)
    runner.checkpoint(RealAdmissionAdministrationState.RUNNER_STARTED)
    checkpoint = runner.record_administration_exception(ValueError("synthetic interruption"))

    assert checkpoint.state is RealAdmissionAdministrationState.ADMINISTRATION_EXCEPTION
    state = json.loads(runner.state_path.read_text(encoding="utf-8"))
    assert state["detail"]["exception_type"] == "ValueError"
    assert not runner.events_path.exists()
    runner.checkpoint(RealAdmissionAdministrationState.FINAL_STOP)


def test_event_log_path_must_not_be_a_link_or_non_file(tmp_path: Path) -> None:
    runner, _legacy_source = _runner(tmp_path)
    runner.events_path.mkdir()

    with pytest.raises(FileBackedRealAdmissionAdministrationRefused, match="event path"):
        runner.checkpoint(RealAdmissionAdministrationState.RUNNER_STARTED)

    assert runner.current_checkpoint is not None
    assert runner.current_checkpoint.state is RealAdmissionAdministrationState.RUNNER_STARTED


def test_resume_requires_the_same_operation_and_continues_the_sequence(tmp_path: Path) -> None:
    runner, _legacy_source = _runner(tmp_path)
    _checkpoint(runner, RealAdmissionAdministrationState.RUNNER_STARTED)

    resumed = FileBackedRealAdmissionAdministrationRunner(
        data_root=runner.result_directory.parent.parent / "synthetic-data",
        result_directory=runner.result_directory,
        operation_id="synthetic-real-admission-qualification",
    )
    resumed.checkpoint(RealAdmissionAdministrationState.PRECHECK_STARTED)
    assert resumed.current_checkpoint is not None
    assert resumed.current_checkpoint.sequence == 2
    with pytest.raises(FileBackedRealAdmissionAdministrationRefused, match="operation_id"):
        FileBackedRealAdmissionAdministrationRunner(
            data_root=runner.result_directory.parent.parent / "synthetic-data",
            result_directory=runner.result_directory,
            operation_id="different-operation",
        )


def test_failed_atomic_replace_preserves_the_prior_authoritative_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner, _legacy_source = _runner(tmp_path)
    runner.checkpoint(RealAdmissionAdministrationState.RUNNER_STARTED)
    prior = runner.state_path.read_bytes()
    monkeypatch.setattr(administration.os, "replace", lambda _source, _destination: (_ for _ in ()).throw(OSError("synthetic replace failure")))

    with pytest.raises(FileBackedRealAdmissionAdministrationWriteError, match="prior state remains authoritative"):
        runner.checkpoint(RealAdmissionAdministrationState.PRECHECK_STARTED)

    assert runner.state_path.read_bytes() == prior
    assert runner.current_checkpoint is not None
    assert runner.current_checkpoint.state is RealAdmissionAdministrationState.RUNNER_STARTED
    assert not list(runner.result_directory.glob("*.tmp"))
