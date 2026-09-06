from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

from torment_service.substrate.detached_real_admission_child_launcher import (
    DetachedRealAdmissionChildLaunchError,
    DetachedRealAdmissionChildLaunchRefused,
    build_detached_real_admission_child_invocation,
    detached_real_admission_creationflags,
    launch_detached_real_admission_external_script_child,
    run_detached_real_admission_import_probe,
)
from torment_service.substrate.detached_real_admission_child_entrypoint import (
    ENTRYPOINT_MODULE,
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
    assert result.entry_invocation_mode == "PYTHON_MODULE"
    assert result.entrypoint_module == ENTRYPOINT_MODULE
    assert result.repository_module_identity == str(
        (_REPOSITORY_ROOT / "torment_service" / "__init__.py").resolve()
    )
    assert result.invocation.arguments[:2] == ("-m", ENTRYPOINT_MODULE)
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
    assert result.sys_path_0 == str(_REPOSITORY_ROOT.resolve())


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


def test_attempt_7_external_script_regression_uses_repository_module_mode_from_unrelated_parent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parent_cwd = tmp_path / "unrelated-parent-cwd"
    parent_cwd.mkdir()
    monkeypatch.chdir(parent_cwd)
    external_directory = tmp_path / "external-administration-body"
    external_directory.mkdir()
    child_result = tmp_path / "external-child-result.json"
    external_script = external_directory / "attempt7_style_capture_body.py"
    external_script.write_text(
        "\n".join(
            (
                "import json",
                "from pathlib import Path",
                "import sys",
                "import torment_service",
                "import torment_service.substrate.real_root_typed_evidence",
                "import torment_service.substrate.writer_freeze_evidence",
                "import torment_service.substrate.file_backed_real_admission_administration_runner",
                "Path(sys.argv[1]).write_text(json.dumps({",
                "    'executable': sys.executable,",
                "    'cwd': str(Path.cwd().resolve()),",
                "    'sys_path_0': sys.path[0],",
                "    'repository_module_identity': str(Path(torment_service.__file__).resolve()),",
                "    'torment_service_importable': True,",
                "}, sort_keys=True), encoding='utf-8')",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    probe = _probe(tmp_path)
    child = launch_detached_real_admission_external_script_child(
        executable=sys.executable,
        repository_root=_REPOSITORY_ROOT,
        external_script=external_script,
        script_arguments=(str(child_result),),
        stdout_path=tmp_path / "external-child.stdout.txt",
        stderr_path=tmp_path / "external-child.stderr.txt",
    )
    assert child.process.wait(timeout=30) == 0

    result = json.loads(child_result.read_text(encoding="utf-8"))
    assert parent_cwd != _REPOSITORY_ROOT
    assert child.arguments[:2] == ("-m", ENTRYPOINT_MODULE)
    assert child.arguments[2:] == (
        "--execute-external-script",
        str(external_script.resolve()),
        str(child_result.resolve()),
    )
    assert result == {
        "cwd": str(_REPOSITORY_ROOT.resolve()),
        "executable": str(Path(sys.executable).resolve()),
        "repository_module_identity": str((_REPOSITORY_ROOT / "torment_service" / "__init__.py").resolve()),
        "sys_path_0": str(_REPOSITORY_ROOT.resolve()),
        "torment_service_importable": True,
    }
    assert probe.invocation.executable == child.executable
    assert probe.invocation.repository_root == child.repository_root
    assert probe.invocation.creationflags == child.creationflags
    assert probe.invocation.entrypoint_module == child.entrypoint_module == ENTRYPOINT_MODULE


def test_probe_real_child_invocation_parity_allows_only_operational_argument_difference(
    tmp_path: Path,
) -> None:
    probe = _probe(tmp_path)
    external_script = tmp_path / "external-administration.py"
    external_script.write_text("# caller-owned synthetic body\n", encoding="utf-8")
    real = build_detached_real_admission_child_invocation(
        executable=sys.executable,
        repository_root=_REPOSITORY_ROOT,
        operational_arguments=("--execute-external-script", str(external_script.resolve())),
    )

    assert probe.invocation.executable == real.executable == Path(sys.executable).resolve()
    assert probe.invocation.repository_root == real.repository_root == _REPOSITORY_ROOT.resolve()
    assert probe.invocation.creationflags == real.creationflags
    assert probe.invocation.entrypoint_module == real.entrypoint_module == ENTRYPOINT_MODULE
    assert probe.invocation.arguments[:2] == real.arguments[:2] == ("-m", ENTRYPOINT_MODULE)
    assert probe.invocation.arguments[2:] != real.arguments[2:]
    assert "-c" not in real.arguments
    assert real.arguments != (str(external_script.resolve()),)


def test_invalid_entrypoint_and_missing_external_script_fail_closed_before_child_launch(tmp_path: Path) -> None:
    with pytest.raises(DetachedRealAdmissionChildLaunchRefused, match="exact repository module"):
        build_detached_real_admission_child_invocation(
            executable=sys.executable,
            repository_root=_REPOSITORY_ROOT,
            operational_arguments=("--import-probe-only", "--result-path", str(tmp_path / "probe.json")),
            entrypoint_module="torment_service.substrate.not_the_qualified_entrypoint",
        )

    missing_script = tmp_path / "missing-external-administration.py"
    with pytest.raises(DetachedRealAdmissionChildLaunchError) as raised:
        launch_detached_real_admission_external_script_child(
            executable=sys.executable,
            repository_root=_REPOSITORY_ROOT,
            external_script=missing_script,
            stdout_path=tmp_path / "missing.stdout.txt",
            stderr_path=tmp_path / "missing.stderr.txt",
        )

    diagnostic = raised.value.diagnostic
    assert diagnostic.executable == str(Path(sys.executable).resolve())
    assert diagnostic.cwd == str(_REPOSITORY_ROOT.resolve())
    assert diagnostic.exception_type == "FileNotFoundError"
    assert str(missing_script.resolve()) in diagnostic.exception_message
