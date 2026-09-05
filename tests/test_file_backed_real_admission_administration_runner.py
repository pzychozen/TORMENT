from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import time

import pytest

import torment_service.substrate.file_backed_real_admission_administration_runner as administration
from torment_service.substrate.file_backed_real_admission_administration_runner import (
    FileBackedRealAdmissionAdministrationRefused,
    FileBackedRealAdmissionAdministrationRunner,
    FileBackedRealAdmissionAdministrationWriteError,
    RealAdmissionAdministrationState,
)


_HEAD = "a" * 40
_ROOT_IDENTITY = "synthetic-data-root-identity-v1"
_OPERATION_ID = "synthetic-real-admission-qualification"


def _paths(tmp_path: Path) -> tuple[Path, Path, Path]:
    data_root = tmp_path / "synthetic-data"
    legacy_source = data_root / "workspaces" / "ws-one" / "source.txt"
    legacy_source.parent.mkdir(parents=True)
    legacy_source.write_bytes(b"synthetic legacy source")
    result_directory = tmp_path / "administration-results" / "operation-one"
    return data_root, legacy_source, result_directory


def _new_runner(
    data_root: Path,
    result_directory: Path,
    *,
    operation_id: str = _OPERATION_ID,
    expected_repository_head: str = _HEAD,
    data_root_identity: str = _ROOT_IDENTITY,
    p1_authorized: bool = False,
    append_events: bool = True,
) -> FileBackedRealAdmissionAdministrationRunner:
    return FileBackedRealAdmissionAdministrationRunner(
        data_root=data_root,
        result_directory=result_directory,
        operation_id=operation_id,
        expected_repository_head=expected_repository_head,
        data_root_identity=data_root_identity,
        p1_authorized=p1_authorized,
        append_events=append_events,
    )


def _runner(
    tmp_path: Path,
    *,
    append_events: bool = True,
    p1_authorized: bool = False,
) -> tuple[FileBackedRealAdmissionAdministrationRunner, Path]:
    data_root, legacy_source, result_directory = _paths(tmp_path)
    return _new_runner(
        data_root,
        result_directory,
        append_events=append_events,
        p1_authorized=p1_authorized,
    ), legacy_source


def _checkpoint(
    runner: FileBackedRealAdmissionAdministrationRunner,
    *states: RealAdmissionAdministrationState,
) -> None:
    for state in states:
        if state in {
            RealAdmissionAdministrationState.P1_PASS,
            RealAdmissionAdministrationState.P1_FAILED_AFTER_DURABLE_STATE,
        }:
            current = runner.current_checkpoint
            if current is not None and not current.run_context.durable_native_state_created:
                runner.mark_durable_native_state_created(detail={"synthetic_durable_marker": True})
        runner.checkpoint(state, detail={"synthetic_state": state.value})


def _event_records(runner: FileBackedRealAdmissionAdministrationRunner) -> list[dict[str, object]]:
    return [json.loads(line) for line in runner.events_path.read_text(encoding="utf-8").splitlines()]


def _state_when_present(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _child_command(data_root: Path, result_directory: Path, operation_id: str, script_body: str) -> list[str]:
    script = f"""
from pathlib import Path
import time
from torment_service.substrate.file_backed_real_admission_administration_runner import (
    FileBackedRealAdmissionAdministrationRunner,
    RealAdmissionAdministrationState,
)
runner = FileBackedRealAdmissionAdministrationRunner(
    data_root=Path({str(data_root)!r}),
    result_directory=Path({str(result_directory)!r}),
    operation_id={operation_id!r},
    expected_repository_head={'b' * 40!r},
    data_root_identity='synthetic-child-root-identity-v1',
    p1_authorized=False,
)
{script_body}
"""
    return [sys.executable, "-c", script]


def _spawn_output_detached_child(command: list[str]) -> subprocess.Popen[bytes]:
    creationflags = getattr(subprocess, "DETACHED_PROCESS", 0)
    return subprocess.Popen(
        command,
        cwd=Path(__file__).resolve().parents[1],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=creationflags,
    )


def test_rejects_a_result_directory_inside_the_supplied_data_root(tmp_path: Path) -> None:
    data_root, _legacy_source, _result_directory = _paths(tmp_path)

    with pytest.raises(FileBackedRealAdmissionAdministrationRefused, match="outside data_root"):
        _new_runner(data_root, data_root / "administration-results" / "forbidden")


def test_atomic_current_state_has_identity_fields_and_optional_external_events(tmp_path: Path) -> None:
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
    assert set(current) == {"contract", "version", "run_context", "state", "sequence", "recorded_at_ns", "detail"}
    assert current["state"] == "FINAL_STOP"
    assert current["sequence"] == 8
    assert current["run_context"] == {
        "operation_id": _OPERATION_ID,
        "expected_repository_head": _HEAD,
        "data_root_identity": _ROOT_IDENTITY,
        "P1_authorized": False,
        "P1_started": False,
        "durable_native_state_created": False,
    }
    assert runner.current_checkpoint is not None
    assert runner.current_checkpoint.state is RealAdmissionAdministrationState.FINAL_STOP
    assert not list(runner.result_directory.glob("*.tmp"))
    events = _event_records(runner)
    assert [event["state"] for event in events] == [
        "RUNNER_STARTED", "PRECHECK_STARTED", "PRECHECK_PASS", "CAPTURE_STARTED",
        "CAPTURE_RETURNED", "DIRECT_PREPARATION_PASS", "P1_NOT_AUTHORIZED", "FINAL_STOP",
    ]
    assert all(event["run_context"] == current["run_context"] for event in events)
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
    p1_authorized = RealAdmissionAdministrationState.P1_READY in states
    runner = _new_runner(
        data_root,
        result_directory,
        operation_id=f"synthetic-{states[-2].value.lower()}",
        p1_authorized=p1_authorized,
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


def test_resume_requires_same_operation_head_root_identity_and_p1_authorization(tmp_path: Path) -> None:
    data_root, _legacy_source, result_directory = _paths(tmp_path)
    runner = _new_runner(data_root, result_directory)
    _checkpoint(runner, RealAdmissionAdministrationState.RUNNER_STARTED)

    resumed = _new_runner(data_root, result_directory)
    resumed.checkpoint(RealAdmissionAdministrationState.PRECHECK_STARTED)
    assert resumed.current_checkpoint is not None
    assert resumed.current_checkpoint.sequence == 2
    for fields, match in (
        ({"operation_id": "different-operation"}, "run identity"),
        ({"expected_repository_head": "c" * 40}, "run identity"),
        ({"data_root_identity": "different-synthetic-root"}, "run identity"),
        ({"p1_authorized": True}, "run identity"),
    ):
        with pytest.raises(FileBackedRealAdmissionAdministrationRefused, match=match):
            _new_runner(data_root, result_directory, **fields)


def test_p1_authorization_is_immutable_and_p1_failure_requires_prior_durable_marker(tmp_path: Path) -> None:
    runner, _legacy_source = _runner(tmp_path, p1_authorized=False)
    _checkpoint(
        runner,
        RealAdmissionAdministrationState.RUNNER_STARTED,
        RealAdmissionAdministrationState.PRECHECK_STARTED,
        RealAdmissionAdministrationState.PRECHECK_PASS,
        RealAdmissionAdministrationState.CAPTURE_STARTED,
        RealAdmissionAdministrationState.CAPTURE_RETURNED,
        RealAdmissionAdministrationState.DIRECT_PREPARATION_PASS,
    )
    with pytest.raises(FileBackedRealAdmissionAdministrationRefused, match="P1_READY"):
        runner.checkpoint(RealAdmissionAdministrationState.P1_READY)
    runner.checkpoint(RealAdmissionAdministrationState.P1_NOT_AUTHORIZED)

    authorized, _legacy_source = _runner(tmp_path / "authorized", p1_authorized=True)
    _checkpoint(
        authorized,
        RealAdmissionAdministrationState.RUNNER_STARTED,
        RealAdmissionAdministrationState.PRECHECK_STARTED,
        RealAdmissionAdministrationState.PRECHECK_PASS,
        RealAdmissionAdministrationState.CAPTURE_STARTED,
        RealAdmissionAdministrationState.CAPTURE_RETURNED,
        RealAdmissionAdministrationState.DIRECT_PREPARATION_PASS,
        RealAdmissionAdministrationState.P1_READY,
        RealAdmissionAdministrationState.P1_STARTED,
    )
    with pytest.raises(FileBackedRealAdmissionAdministrationRefused, match="durable native state"):
        authorized.checkpoint(RealAdmissionAdministrationState.P1_FAILED_AFTER_DURABLE_STATE)


def test_failed_atomic_replace_preserves_the_prior_authoritative_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner, _legacy_source = _runner(tmp_path)
    runner.checkpoint(RealAdmissionAdministrationState.RUNNER_STARTED)
    prior = runner.state_path.read_bytes()
    monkeypatch.setattr(
        administration.os,
        "replace",
        lambda _source, _destination: (_ for _ in ()).throw(OSError("synthetic replace failure")),
    )

    with pytest.raises(FileBackedRealAdmissionAdministrationWriteError, match="prior state remains authoritative"):
        runner.checkpoint(RealAdmissionAdministrationState.PRECHECK_STARTED)

    assert runner.state_path.read_bytes() == prior
    assert runner.current_checkpoint is not None
    assert runner.current_checkpoint.state is RealAdmissionAdministrationState.RUNNER_STARTED
    assert not list(runner.result_directory.glob("*.tmp"))


def test_child_output_can_be_detached_and_final_state_recovers_without_stdout(tmp_path: Path) -> None:
    data_root = tmp_path / "synthetic-child-data"
    result_directory = tmp_path / "administration-results" / "detached-child"
    command = _child_command(
        data_root,
        result_directory,
        "synthetic-detached-child",
        """
for state in (
    RealAdmissionAdministrationState.RUNNER_STARTED,
    RealAdmissionAdministrationState.PRECHECK_STARTED,
    RealAdmissionAdministrationState.PRECHECK_PASS,
    RealAdmissionAdministrationState.CAPTURE_STARTED,
):
    runner.checkpoint(state, detail={"child_state": state.value})
time.sleep(1.0)
for state in (
    RealAdmissionAdministrationState.CAPTURE_RETURNED,
    RealAdmissionAdministrationState.DIRECT_PREPARATION_PASS,
    RealAdmissionAdministrationState.P1_NOT_AUTHORIZED,
    RealAdmissionAdministrationState.FINAL_STOP,
):
    runner.checkpoint(state, detail={"child_state": state.value})
""",
    )
    child = _spawn_output_detached_child(command)
    try:
        time.sleep(0.2)
        assert child.poll() is None
        assert child.wait(timeout=15) == 0
    finally:
        if child.poll() is None:
            child.terminate()
            child.wait(timeout=15)

    resumed = _new_runner(
        data_root,
        result_directory,
        operation_id="synthetic-detached-child",
        expected_repository_head="b" * 40,
        data_root_identity="synthetic-child-root-identity-v1",
    )
    assert resumed.current_checkpoint is not None
    assert resumed.current_checkpoint.state is RealAdmissionAdministrationState.FINAL_STOP
    assert json.loads(resumed.state_path.read_text(encoding="utf-8"))["state"] == "FINAL_STOP"


def test_interrupted_child_leaves_last_complete_capture_started_checkpoint(tmp_path: Path) -> None:
    data_root = tmp_path / "synthetic-interrupted-data"
    result_directory = tmp_path / "administration-results" / "interrupted-child"
    command = _child_command(
        data_root,
        result_directory,
        "synthetic-interrupted-child",
        """
for state in (
    RealAdmissionAdministrationState.RUNNER_STARTED,
    RealAdmissionAdministrationState.PRECHECK_STARTED,
    RealAdmissionAdministrationState.PRECHECK_PASS,
    RealAdmissionAdministrationState.CAPTURE_STARTED,
):
    runner.checkpoint(state, detail={"child_state": state.value})
time.sleep(30.0)
""",
    )
    child = _spawn_output_detached_child(command)
    try:
        deadline = time.monotonic() + 15
        observed: dict[str, object] | None = None
        while time.monotonic() < deadline:
            observed = _state_when_present(result_directory / "administration_state.json")
            if observed is not None and observed.get("state") == "CAPTURE_STARTED":
                break
            time.sleep(0.05)
        assert observed is not None
        assert observed["state"] == "CAPTURE_STARTED"
        child.terminate()
        child.wait(timeout=15)
    finally:
        if child.poll() is None:
            child.terminate()
            child.wait(timeout=15)

    resumed = _new_runner(
        data_root,
        result_directory,
        operation_id="synthetic-interrupted-child",
        expected_repository_head="b" * 40,
        data_root_identity="synthetic-child-root-identity-v1",
    )
    assert resumed.current_checkpoint is not None
    assert resumed.current_checkpoint.state is RealAdmissionAdministrationState.CAPTURE_STARTED
    assert [event["state"] for event in _event_records(resumed)] == [
        "RUNNER_STARTED", "PRECHECK_STARTED", "PRECHECK_PASS", "CAPTURE_STARTED",
    ]


def test_p1_callback_observes_durable_started_checkpoint_before_its_first_mutation(tmp_path: Path) -> None:
    runner, _legacy_source = _runner(tmp_path, p1_authorized=True)
    _checkpoint(
        runner,
        RealAdmissionAdministrationState.RUNNER_STARTED,
        RealAdmissionAdministrationState.PRECHECK_STARTED,
        RealAdmissionAdministrationState.PRECHECK_PASS,
        RealAdmissionAdministrationState.CAPTURE_STARTED,
        RealAdmissionAdministrationState.CAPTURE_RETURNED,
        RealAdmissionAdministrationState.DIRECT_PREPARATION_PASS,
        RealAdmissionAdministrationState.P1_READY,
    )
    before = json.loads(runner.state_path.read_text(encoding="utf-8"))
    assert before["state"] == "P1_READY"
    assert before["run_context"]["P1_authorized"] is True
    assert before["run_context"]["P1_started"] is False
    assert before["run_context"]["durable_native_state_created"] is False
    marker = runner.result_directory.parent / "synthetic-callback-first-mutation.txt"

    def fake_p1(callback_runner: FileBackedRealAdmissionAdministrationRunner) -> str:
        boundary = json.loads(callback_runner.state_path.read_text(encoding="utf-8"))
        assert boundary["state"] == "P1_STARTED"
        assert boundary["run_context"]["P1_authorized"] is True
        assert boundary["run_context"]["P1_started"] is True
        assert boundary["run_context"]["durable_native_state_created"] is False
        marker.write_text("synthetic fake callback mutation", encoding="utf-8")
        return "called"

    assert runner.invoke_p1(fake_p1, detail={"synthetic_boundary": "before_callback"}) == "called"
    assert marker.read_text(encoding="utf-8") == "synthetic fake callback mutation"


def test_fake_durable_failure_retains_artifact_and_disables_retry(tmp_path: Path) -> None:
    runner, _legacy_source = _runner(tmp_path, p1_authorized=True)
    _checkpoint(
        runner,
        RealAdmissionAdministrationState.RUNNER_STARTED,
        RealAdmissionAdministrationState.PRECHECK_STARTED,
        RealAdmissionAdministrationState.PRECHECK_PASS,
        RealAdmissionAdministrationState.CAPTURE_STARTED,
        RealAdmissionAdministrationState.CAPTURE_RETURNED,
        RealAdmissionAdministrationState.DIRECT_PREPARATION_PASS,
        RealAdmissionAdministrationState.P1_READY,
    )
    fake_native_artifact = runner.result_directory.parent / "synthetic-native-artifact.txt"

    def fake_p1(callback_runner: FileBackedRealAdmissionAdministrationRunner) -> None:
        assert callback_runner.current_checkpoint is not None
        assert callback_runner.current_checkpoint.state is RealAdmissionAdministrationState.P1_STARTED
        fake_native_artifact.write_text("synthetic durable state", encoding="utf-8")
        callback_runner.mark_durable_native_state_created(detail={"artifact": fake_native_artifact.name})
        raise RuntimeError("synthetic failure after fake durable state")

    with pytest.raises(RuntimeError, match="synthetic failure"):
        runner.invoke_p1(fake_p1)

    assert fake_native_artifact.read_text(encoding="utf-8") == "synthetic durable state"
    assert runner.current_checkpoint is not None
    assert runner.current_checkpoint.state is RealAdmissionAdministrationState.P1_FAILED_AFTER_DURABLE_STATE
    state = json.loads(runner.state_path.read_text(encoding="utf-8"))
    assert state["run_context"]["P1_started"] is True
    assert state["run_context"]["durable_native_state_created"] is True
    with pytest.raises(FileBackedRealAdmissionAdministrationRefused, match="not allowed"):
        runner.invoke_p1(fake_p1)


def test_capture_and_direct_preparation_details_are_recoverable_from_events(tmp_path: Path) -> None:
    runner, _legacy_source = _runner(tmp_path)
    capture_detail = {
        "writer_freeze_operation_id": "synthetic-freeze-001",
        "payload_digest": "synthetic-payload-digest",
        "writer_evidence_witness_relationship": {"writer": "writer-1", "witness": "witness-1"},
        "stability_delta": {"before": 0, "after": 0},
        "file_count": 3,
        "tree_digest": "synthetic-tree-digest",
        "jobs": ["capture-job-1"],
        "listener": {"identity": "synthetic-listener"},
        "covered_writer": {"identity": "synthetic-writer"},
    }
    preparation_detail = {
        "description_identity": "synthetic-description-001",
        "description_digest": "synthetic-description-digest",
        "counts": {"workspaces": 1, "sources": 3},
        "posture": "synthetic-read-only",
        "dispositions": {"workspace-one": "admissible"},
        "unknown_scope_keys": ["synthetic-unknown-key"],
        "empty_private_count": 0,
        "geometry_summary": {"root": "synthetic", "files": 3},
    }
    _checkpoint(
        runner,
        RealAdmissionAdministrationState.RUNNER_STARTED,
        RealAdmissionAdministrationState.PRECHECK_STARTED,
        RealAdmissionAdministrationState.PRECHECK_PASS,
        RealAdmissionAdministrationState.CAPTURE_STARTED,
    )
    runner.checkpoint(RealAdmissionAdministrationState.CAPTURE_RETURNED, detail=capture_detail)
    runner.checkpoint(RealAdmissionAdministrationState.DIRECT_PREPARATION_PASS, detail=preparation_detail)
    runner.checkpoint(RealAdmissionAdministrationState.P1_NOT_AUTHORIZED)
    runner.checkpoint(RealAdmissionAdministrationState.FINAL_STOP)

    records = {record["state"]: record for record in _event_records(runner)}
    assert records["CAPTURE_RETURNED"]["detail"] == capture_detail
    assert records["DIRECT_PREPARATION_PASS"]["detail"] == preparation_detail


def test_preparation_refusal_and_unexpected_exception_details_are_recoverable(tmp_path: Path) -> None:
    runner, _legacy_source = _runner(tmp_path)
    _checkpoint(
        runner,
        RealAdmissionAdministrationState.RUNNER_STARTED,
        RealAdmissionAdministrationState.PRECHECK_STARTED,
        RealAdmissionAdministrationState.PRECHECK_PASS,
        RealAdmissionAdministrationState.CAPTURE_STARTED,
        RealAdmissionAdministrationState.CAPTURE_RETURNED,
    )
    refusal_detail = {"reason": "synthetic source refusal", "unknown_scope_keys": ["unmapped"]}
    runner.checkpoint(RealAdmissionAdministrationState.DIRECT_PREPARATION_REFUSED, detail=refusal_detail)
    runner.checkpoint(RealAdmissionAdministrationState.FINAL_STOP)
    assert {
        record["state"]: record["detail"] for record in _event_records(runner)
    }["DIRECT_PREPARATION_REFUSED"] == refusal_detail

    exceptional, _legacy_source = _runner(tmp_path / "exceptional")
    exceptional.checkpoint(RealAdmissionAdministrationState.RUNNER_STARTED)
    exceptional.record_administration_exception(RuntimeError("synthetic unexpected exception"))
    assert {
        record["state"]: record["detail"] for record in _event_records(exceptional)
    }["ADMINISTRATION_EXCEPTION"] == {
        "exception_type": "RuntimeError",
        "exception_message": "synthetic unexpected exception",
    }
