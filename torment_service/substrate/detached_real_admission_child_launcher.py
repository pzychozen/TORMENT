"""Deterministic detached-child launch support for admission administration.

This module has no source, writer, listener, SQLite, migration, or admission
authority.  It binds a supplied interpreter and repository package root to a
child process so a future external administration can retain child diagnostics
without relying on its attached terminal.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import subprocess
from typing import Sequence
from uuid import uuid4


_PROBE_CONTRACT = "TORMENT_DETACHED_REAL_ADMISSION_IMPORT_PROBE"
_PROBE_VERSION = 1


class DetachedRealAdmissionChildLaunchRefused(RuntimeError):
    """A detached child request lacks its required explicit launch context."""


@dataclass(frozen=True)
class DetachedRealAdmissionChildLaunchDiagnostic:
    """Bounded failure facts sufficient to stop before a real administration."""

    executable: str
    cwd: str
    exception_type: str
    exception_message: str

    def __post_init__(self) -> None:
        for label in ("executable", "cwd", "exception_type", "exception_message"):
            value = getattr(self, label)
            if not isinstance(value, str) or not value:
                raise DetachedRealAdmissionChildLaunchRefused(f"launch diagnostic {label} must be non-empty text")

    def payload(self) -> dict[str, str]:
        return {
            "executable": self.executable,
            "cwd": self.cwd,
            "exception_type": self.exception_type,
            "exception_message": self.exception_message,
        }


class DetachedRealAdmissionChildLaunchError(RuntimeError):
    """A child could not launch or its required import probe did not pass."""

    def __init__(self, diagnostic: DetachedRealAdmissionChildLaunchDiagnostic) -> None:
        self.diagnostic = diagnostic
        super().__init__(
            f"detached child launch failed: {diagnostic.exception_type}: {diagnostic.exception_message}"
        )


@dataclass(frozen=True)
class DetachedRealAdmissionChildProcess:
    """A launched process and the exact immutable context supplied to it."""

    process: subprocess.Popen[bytes]
    executable: Path
    repository_root: Path
    stdout_path: Path
    stderr_path: Path
    creationflags: int


@dataclass(frozen=True)
class DetachedRealAdmissionImportProbeResult:
    """The child's file-backed import-only result, independent of stdout."""

    passed: bool
    cwd: str
    executable: str
    exception_type: str | None
    exception_message: str | None

    def __post_init__(self) -> None:
        if not isinstance(self.passed, bool):
            raise DetachedRealAdmissionChildLaunchRefused("import probe passed must be boolean")
        for label in ("cwd", "executable"):
            value = getattr(self, label)
            if not isinstance(value, str) or not value:
                raise DetachedRealAdmissionChildLaunchRefused(f"import probe {label} must be non-empty text")
        if self.passed:
            if self.exception_type is not None or self.exception_message is not None:
                raise DetachedRealAdmissionChildLaunchRefused("passing import probe cannot retain an exception")
        elif not isinstance(self.exception_type, str) or not isinstance(self.exception_message, str):
            raise DetachedRealAdmissionChildLaunchRefused("failing import probe must retain its exact exception")


def detached_real_admission_creationflags() -> int:
    """Return the platform's detached child flags without modifying its environment."""

    return getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)


def launch_detached_real_admission_child(
    *,
    executable: str | Path,
    repository_root: str | Path,
    arguments: Sequence[str],
    stdout_path: str | Path,
    stderr_path: str | Path,
) -> DetachedRealAdmissionChildProcess:
    """Launch one child with explicit executable, repository CWD, and detached stdio.

    The caller owns the child program and every administrative authority.  This
    function never searches ``PATH``, changes environment variables, or reads
    a data root.
    """

    root = _validated_repository_root(repository_root)
    interpreter = _validated_executable(executable, root)
    child_arguments = _validated_arguments(arguments)
    stdout = _validated_output_path(stdout_path, "stdout_path")
    stderr = _validated_output_path(stderr_path, "stderr_path")
    if stdout == stderr:
        raise DetachedRealAdmissionChildLaunchRefused("stdout_path and stderr_path must be distinct")
    try:
        stdout.parent.mkdir(parents=True, exist_ok=True)
        stderr.parent.mkdir(parents=True, exist_ok=True)
        with stdout.open("xb") as stdout_stream, stderr.open("xb") as stderr_stream:
            process = subprocess.Popen(
                [str(interpreter), *child_arguments],
                executable=str(interpreter),
                cwd=str(root),
                stdin=subprocess.DEVNULL,
                stdout=stdout_stream,
                stderr=stderr_stream,
                creationflags=detached_real_admission_creationflags(),
            )
    except OSError as exc:
        raise DetachedRealAdmissionChildLaunchError(
            _diagnostic(interpreter, root, exc)
        ) from exc
    return DetachedRealAdmissionChildProcess(
        process=process,
        executable=interpreter,
        repository_root=root,
        stdout_path=stdout,
        stderr_path=stderr,
        creationflags=detached_real_admission_creationflags(),
    )


def run_detached_real_admission_import_probe(
    *,
    executable: str | Path,
    repository_root: str | Path,
    stdout_path: str | Path,
    stderr_path: str | Path,
    result_path: str | Path,
    timeout_seconds: float = 30.0,
) -> DetachedRealAdmissionImportProbeResult:
    """Run and recover an import-only child using the real child's exact context."""

    root = _validated_repository_root(repository_root)
    interpreter = _validated_executable(executable, root)
    probe_path = _validated_output_path(result_path, "result_path")
    stdout = _validated_output_path(stdout_path, "stdout_path")
    stderr = _validated_output_path(stderr_path, "stderr_path")
    if len({probe_path, stdout, stderr}) != 3:
        raise DetachedRealAdmissionChildLaunchRefused(
            "import probe result, stdout, and stderr paths must be distinct"
        )
    probe_path.parent.mkdir(parents=True, exist_ok=True)
    child = launch_detached_real_admission_child(
        executable=interpreter,
        repository_root=root,
        arguments=("-c", _import_probe_program(probe_path)),
        stdout_path=stdout,
        stderr_path=stderr,
    )
    try:
        child.process.wait(timeout=_validated_timeout(timeout_seconds))
    except subprocess.TimeoutExpired as exc:
        raise DetachedRealAdmissionChildLaunchError(
            _diagnostic(child.executable, child.repository_root, exc)
        ) from exc
    result = _read_import_probe_result(
        probe_path,
        executable=child.executable,
        repository_root=child.repository_root,
    )
    if not result.passed:
        raise DetachedRealAdmissionChildLaunchError(
            DetachedRealAdmissionChildLaunchDiagnostic(
                executable=result.executable,
                cwd=result.cwd,
                exception_type=result.exception_type or "UnknownImportProbeFailure",
                exception_message=result.exception_message or "import probe failed without exception detail",
            )
        )
    if child.process.returncode != 0:
        error = RuntimeError(f"import probe exited with return code {child.process.returncode}")
        raise DetachedRealAdmissionChildLaunchError(
            _diagnostic(child.executable, child.repository_root, error)
        )
    return result


def _validated_repository_root(value: str | Path) -> Path:
    if not isinstance(value, (str, Path)) or not str(value).strip():
        raise DetachedRealAdmissionChildLaunchRefused("repository_root must be an explicit non-empty path")
    root = Path(value).expanduser().resolve(strict=False)
    package = root / "torment_service"
    if not root.is_dir() or not package.is_dir() or not (package / "__init__.py").is_file():
        raise DetachedRealAdmissionChildLaunchRefused(
            "repository_root must contain an importable torment_service package"
        )
    return root


def _validated_executable(value: str | Path, root: Path) -> Path:
    if not isinstance(value, (str, Path)) or not str(value).strip():
        raise DetachedRealAdmissionChildLaunchRefused("executable must be an explicit non-empty path")
    executable = Path(value).expanduser().resolve(strict=False)
    if not executable.is_file():
        error = FileNotFoundError(f"explicit child executable does not exist: {executable}")
        raise DetachedRealAdmissionChildLaunchError(_diagnostic(executable, root, error))
    return executable


def _validated_arguments(value: Sequence[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence) or not value:
        raise DetachedRealAdmissionChildLaunchRefused("child arguments must be a non-empty sequence of strings")
    if any(not isinstance(item, str) for item in value):
        raise DetachedRealAdmissionChildLaunchRefused("child arguments must be strings")
    return tuple(value)


def _validated_output_path(value: str | Path, label: str) -> Path:
    if not isinstance(value, (str, Path)) or not str(value).strip():
        raise DetachedRealAdmissionChildLaunchRefused(f"{label} must be an explicit non-empty path")
    return Path(value).expanduser().resolve(strict=False)


def _validated_timeout(value: float) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
        raise DetachedRealAdmissionChildLaunchRefused("timeout_seconds must be positive")
    return float(value)


def _diagnostic(
    executable: Path,
    root: Path,
    exception: BaseException,
) -> DetachedRealAdmissionChildLaunchDiagnostic:
    return DetachedRealAdmissionChildLaunchDiagnostic(
        executable=str(executable),
        cwd=str(root),
        exception_type=type(exception).__name__,
        exception_message=str(exception),
    )


def _import_probe_program(result_path: Path) -> str:
    """Return an import-only child program that atomically retains its result."""

    encoded_result_path = json.dumps(str(result_path))
    return f"""
import json
import os
from pathlib import Path
import sys
from uuid import uuid4

result_path = Path({encoded_result_path})
result = {{
    \"contract\": {_PROBE_CONTRACT!r},
    \"version\": {_PROBE_VERSION},
    \"passed\": False,
    \"cwd\": str(Path.cwd().resolve()),
    \"executable\": sys.executable,
    \"exception_type\": None,
    \"exception_message\": None,
}}
try:
    import torment_service
    import torment_service.substrate.real_root_typed_evidence
    import torment_service.substrate.writer_freeze_evidence
    import torment_service.substrate.file_backed_real_admission_administration_runner
except BaseException as exc:
    result[\"exception_type\"] = type(exc).__name__
    result[\"exception_message\"] = str(exc)
else:
    result[\"passed\"] = True
temporary = result_path.with_name(f\".{{result_path.name}}.{{uuid4().hex}}.tmp\")
with temporary.open(\"x\", encoding=\"utf-8\", newline=\"\\n\") as stream:
    stream.write(json.dumps(result, ensure_ascii=True, allow_nan=False, separators=(\",\", \":\"), sort_keys=True) + \"\\n\")
    stream.flush()
    os.fsync(stream.fileno())
os.replace(temporary, result_path)
raise SystemExit(0 if result[\"passed\"] else 1)
"""


def _read_import_probe_result(
    path: Path,
    *,
    executable: Path,
    repository_root: Path,
) -> DetachedRealAdmissionImportProbeResult:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DetachedRealAdmissionChildLaunchError(
            DetachedRealAdmissionChildLaunchDiagnostic(
                executable=str(executable),
                cwd=str(repository_root),
                exception_type=type(exc).__name__,
                exception_message=str(exc),
            )
        ) from exc
    required = {
        "contract", "version", "passed", "cwd", "executable", "exception_type", "exception_message",
    }
    if not isinstance(value, dict) or set(value) != required:
        raise DetachedRealAdmissionChildLaunchRefused("import probe result shape is invalid")
    if value["contract"] != _PROBE_CONTRACT or value["version"] != _PROBE_VERSION:
        raise DetachedRealAdmissionChildLaunchRefused("import probe result contract is unsupported")
    return DetachedRealAdmissionImportProbeResult(
        passed=value["passed"],
        cwd=value["cwd"],
        executable=value["executable"],
        exception_type=value["exception_type"],
        exception_message=value["exception_message"],
    )


__all__ = [
    "DetachedRealAdmissionChildLaunchDiagnostic",
    "DetachedRealAdmissionChildLaunchError",
    "DetachedRealAdmissionChildLaunchRefused",
    "DetachedRealAdmissionChildProcess",
    "DetachedRealAdmissionImportProbeResult",
    "detached_real_admission_creationflags",
    "launch_detached_real_admission_child",
    "run_detached_real_admission_import_probe",
]
