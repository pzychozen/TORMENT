from __future__ import annotations

from pathlib import Path
import sys

import pytest

from torment_service.substrate.detached_real_admission_child_launcher import (
    DetachedRealAdmissionChildLaunchError,
    DetachedRealAdmissionChildLaunchRefused,
    detached_real_admission_creationflags,
    run_detached_real_admission_import_probe,
)


_REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def _probe(
    tmp_path: Path,
    *,
    executable: Path | str = sys.executable,
    repository_root: Path | str = _REPOSITORY_ROOT,
):
    result_directory = tmp_path / "external-administration-results"
    return run_detached_real_admission_import_probe(
        executable=executable,
        repository_root=repository_root,
        stdout_path=result_directory / "probe.stdout.txt",
        stderr_path=result_directory / "probe.stderr.txt",
        result_path=result_directory / "probe.result.json",
    )


def test_detached_import_probe_uses_explicit_repository_root_from_repository_parent(tmp_path: Path) -> None:
    result = _probe(tmp_path)

    assert result.passed is True
    assert result.cwd == str(_REPOSITORY_ROOT.resolve())
    assert result.executable == str(Path(sys.executable).resolve())
    assert result.exception_type is None
    assert result.exception_message is None


def test_detached_import_probe_is_independent_of_the_parent_current_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    unrelated_parent_directory = tmp_path / "unrelated-parent-current-directory"
    unrelated_parent_directory.mkdir()
    monkeypatch.chdir(unrelated_parent_directory)

    result = _probe(tmp_path)

    assert result.passed is True
    assert result.cwd == str(_REPOSITORY_ROOT.resolve())


def test_invalid_repository_root_refuses_before_any_child_launch(tmp_path: Path) -> None:
    result_directory = tmp_path / "external-administration-results"
    invalid_root = tmp_path / "not-a-repository"

    with pytest.raises(DetachedRealAdmissionChildLaunchRefused, match="importable torment_service"):
        run_detached_real_admission_import_probe(
            executable=sys.executable,
            repository_root=invalid_root,
            stdout_path=result_directory / "probe.stdout.txt",
            stderr_path=result_directory / "probe.stderr.txt",
            result_path=result_directory / "probe.result.json",
        )

    assert not result_directory.exists()


def test_nonexistent_explicit_interpreter_fails_closed_with_exact_diagnostic(tmp_path: Path) -> None:
    missing_executable = tmp_path / "missing-qualified-python.exe"

    with pytest.raises(DetachedRealAdmissionChildLaunchError) as raised:
        _probe(tmp_path, executable=missing_executable)

    diagnostic = raised.value.diagnostic
    assert diagnostic.executable == str(missing_executable.resolve())
    assert diagnostic.cwd == str(_REPOSITORY_ROOT.resolve())
    assert diagnostic.exception_type == "FileNotFoundError"
    assert str(missing_executable.resolve()) in diagnostic.exception_message


def test_existing_but_wrong_explicit_executable_fails_closed_with_requested_context(tmp_path: Path) -> None:
    wrong_executable = tmp_path / "wrong-qualified-python.exe"
    wrong_executable.write_bytes(b"not a python executable")

    with pytest.raises(DetachedRealAdmissionChildLaunchError) as raised:
        _probe(tmp_path, executable=wrong_executable)

    diagnostic = raised.value.diagnostic
    assert diagnostic.executable == str(wrong_executable.resolve())
    assert diagnostic.cwd == str(_REPOSITORY_ROOT.resolve())
    assert diagnostic.exception_type.endswith("Error")
    assert diagnostic.exception_message


def test_import_result_is_recovered_from_file_backed_probe_not_attached_output(tmp_path: Path) -> None:
    result = _probe(tmp_path)
    result_directory = tmp_path / "external-administration-results"

    assert result.passed is True
    assert (result_directory / "probe.result.json").is_file()
    assert (result_directory / "probe.stdout.txt").is_file()
    assert (result_directory / "probe.stderr.txt").is_file()
    assert detached_real_admission_creationflags() >= 0


def test_attempt_6_regression_parent_outside_repository_still_binds_child_context(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Do not reproduce ModuleNotFoundError; prove the deterministic fix instead."""

    parent_cwd = tmp_path / "attempt-6-style-external-administration-directory"
    parent_cwd.mkdir()
    monkeypatch.chdir(parent_cwd)

    result = _probe(tmp_path)

    assert parent_cwd != _REPOSITORY_ROOT
    assert result.passed is True
    assert result.cwd == str(_REPOSITORY_ROOT.resolve())
    assert result.executable == str(Path(sys.executable).resolve())
