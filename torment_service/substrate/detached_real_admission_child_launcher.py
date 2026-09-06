"""Deterministic detached-child launch support for admission administration.

This module has no source, writer, listener, SQLite, migration, or admission
authority.  It binds a supplied interpreter and repository package root to a
child process so a future external administration can retain child diagnostics
without relying on its attached terminal.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
from typing import Sequence
from torment_service.substrate.detached_real_admission_child_entrypoint import (
    ENTRYPOINT_MODULE,
    IMPORT_PROBE_CONTRACT,
    IMPORT_PROBE_VERSION,
)


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
class DetachedRealAdmissionChildInvocation:
    """The exact, module-mode command context for a detached child."""

    executable: Path
    repository_root: Path
    arguments: tuple[str, ...]
    entrypoint_module: str
    creationflags: int


@dataclass(frozen=True)
class DetachedRealAdmissionChildProcess:
    """A launched process and its immutable module-mode invocation."""

    process: subprocess.Popen[bytes]
    invocation: DetachedRealAdmissionChildInvocation
    stdout_path: Path
    stderr_path: Path

    @property
    def executable(self) -> Path:
        return self.invocation.executable

    @property
    def repository_root(self) -> Path:
        return self.invocation.repository_root

    @property
    def arguments(self) -> tuple[str, ...]:
        return self.invocation.arguments

    @property
    def entrypoint_module(self) -> str:
        return self.invocation.entrypoint_module

    @property
    def creationflags(self) -> int:
        return self.invocation.creationflags


@dataclass(frozen=True)
class DetachedRealAdmissionImportProbeResult:
    """The exact module-mode, file-backed import-only child result."""

    passed: bool
    cwd: str
    executable: str
    sys_path_0: str
    entry_invocation_mode: str
    entrypoint_module: str
    repository_module_identity: str | None
    exception_type: str | None
    exception_message: str | None
    invocation: DetachedRealAdmissionChildInvocation

    def __post_init__(self) -> None:
        if not isinstance(self.passed, bool):
            raise DetachedRealAdmissionChildLaunchRefused("import probe passed must be boolean")
        for label in ("cwd", "executable", "entry_invocation_mode", "entrypoint_module"):
            value = getattr(self, label)
            if not isinstance(value, str) or not value:
                raise DetachedRealAdmissionChildLaunchRefused(f"import probe {label} must be non-empty text")
        if not isinstance(self.sys_path_0, str):
            raise DetachedRealAdmissionChildLaunchRefused("import probe sys_path_0 must be text")
        if self.passed:
            if (
                self.exception_type is not None
                or self.exception_message is not None
                or not isinstance(self.repository_module_identity, str)
                or not self.repository_module_identity
            ):
                raise DetachedRealAdmissionChildLaunchRefused("passing import probe cannot retain an exception")
        elif (
            not isinstance(self.exception_type, str)
            or not isinstance(self.exception_message, str)
            or self.repository_module_identity is not None
        ):
            raise DetachedRealAdmissionChildLaunchRefused("failing import probe must retain its exact exception")


def detached_real_admission_creationflags() -> int:
    """Return the platform's detached child flags without modifying its environment."""

    return getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)


def build_detached_real_admission_child_invocation(
    *,
    executable: str | Path,
    repository_root: str | Path,
    operational_arguments: Sequence[str],
    entrypoint_module: str = ENTRYPOINT_MODULE,
) -> DetachedRealAdmissionChildInvocation:
    """Build one fail-closed, repository-owned ``python -m`` invocation."""

    root = _validated_repository_root(repository_root)
    interpreter = _validated_executable(executable, root)
    module = _validated_entrypoint_module(entrypoint_module, root)
    operation = _validated_operational_arguments(operational_arguments)
    return DetachedRealAdmissionChildInvocation(
        executable=interpreter,
        repository_root=root,
        arguments=("-m", module, *operation),
        entrypoint_module=module,
        creationflags=detached_real_admission_creationflags(),
    )


def launch_detached_real_admission_child(
    *,
    executable: str | Path,
    repository_root: str | Path,
    operational_arguments: Sequence[str],
    stdout_path: str | Path,
    stderr_path: str | Path,
    entrypoint_module: str = ENTRYPOINT_MODULE,
) -> DetachedRealAdmissionChildProcess:
    """Launch only the qualified repository module with explicit context.

    This function never launches raw ``-c`` or external-script argument shapes.
    The caller retains every source, writer, SQLite, and P1 authority.
    """

    invocation = build_detached_real_admission_child_invocation(
        executable=executable,
        repository_root=repository_root,
        operational_arguments=operational_arguments,
        entrypoint_module=entrypoint_module,
    )
    return _launch_detached_real_admission_invocation(
        invocation,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
    )


def launch_detached_real_admission_external_script_child(
    *,
    executable: str | Path,
    repository_root: str | Path,
    external_script: str | Path,
    script_arguments: Sequence[str] = (),
    stdout_path: str | Path,
    stderr_path: str | Path,
) -> DetachedRealAdmissionChildProcess:
    """Launch a caller-supplied script only through the module entrypoint."""

    root = _validated_repository_root(repository_root)
    interpreter = _validated_executable(executable, root)
    script = _validated_external_script(external_script, interpreter, root)
    arguments = _validated_arguments(script_arguments, "script_arguments")
    invocation = build_detached_real_admission_child_invocation(
        executable=interpreter,
        repository_root=root,
        operational_arguments=("--execute-external-script", str(script), *arguments),
    )
    return _launch_detached_real_admission_invocation(
        invocation,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
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
    """Run the future child's exact ``python -m`` entrypoint in probe mode."""

    root = _validated_repository_root(repository_root)
    interpreter = _validated_executable(executable, root)
    probe_path = _validated_output_path(result_path, "result_path")
    stdout = _validated_output_path(stdout_path, "stdout_path")
    stderr = _validated_output_path(stderr_path, "stderr_path")
    if len({probe_path, stdout, stderr}) != 3:
        raise DetachedRealAdmissionChildLaunchRefused(
            "import probe result, stdout, and stderr paths must be distinct"
        )
    invocation = build_detached_real_admission_child_invocation(
        executable=interpreter,
        repository_root=root,
        operational_arguments=("--import-probe-only", "--result-path", str(probe_path)),
    )
    child = _launch_detached_real_admission_invocation(
        invocation,
        stdout_path=stdout,
        stderr_path=stderr,
    )
    try:
        child.process.wait(timeout=_validated_timeout(timeout_seconds))
    except subprocess.TimeoutExpired as exc:
        raise DetachedRealAdmissionChildLaunchError(
            _diagnostic(child.executable, child.repository_root, exc)
        ) from exc
    result = _read_import_probe_result(probe_path, invocation=invocation)
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


def _validated_entrypoint_module(value: str, root: Path) -> str:
    if not isinstance(value, str) or value != ENTRYPOINT_MODULE:
        raise DetachedRealAdmissionChildLaunchRefused(
            f"entrypoint_module must be the exact repository module {ENTRYPOINT_MODULE!r}"
        )
    module_path = root.joinpath(*value.split(".")).with_suffix(".py")
    if not module_path.is_file():
        raise DetachedRealAdmissionChildLaunchRefused(
            f"exact repository entrypoint module does not exist: {module_path}"
        )
    return value


def _validated_arguments(value: Sequence[str], label: str) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise DetachedRealAdmissionChildLaunchRefused(f"{label} must be a sequence of strings")
    if any(not isinstance(item, str) for item in value):
        raise DetachedRealAdmissionChildLaunchRefused(f"{label} must contain only strings")
    return tuple(value)


def _validated_operational_arguments(value: Sequence[str]) -> tuple[str, ...]:
    arguments = _validated_arguments(value, "operational_arguments")
    if not arguments:
        raise DetachedRealAdmissionChildLaunchRefused("operational_arguments must be non-empty")
    if arguments[0] not in {"--import-probe-only", "--execute-external-script"}:
        raise DetachedRealAdmissionChildLaunchRefused(
            "operational_arguments must select the exact repository entrypoint mode"
        )
    return arguments


def _validated_external_script(value: str | Path, executable: Path, root: Path) -> Path:
    if not isinstance(value, (str, Path)) or not str(value).strip():
        raise DetachedRealAdmissionChildLaunchRefused("external_script must be an explicit non-empty path")
    script = Path(value).expanduser().resolve(strict=False)
    if not script.is_file():
        error = FileNotFoundError(f"explicit external administration script does not exist: {script}")
        raise DetachedRealAdmissionChildLaunchError(_diagnostic(executable, root, error))
    if script.suffix.lower() != ".py":
        raise DetachedRealAdmissionChildLaunchRefused("external_script must name an explicit .py file")
    return script


def _validated_output_path(value: str | Path, label: str) -> Path:
    if not isinstance(value, (str, Path)) or not str(value).strip():
        raise DetachedRealAdmissionChildLaunchRefused(f"{label} must be an explicit non-empty path")
    return Path(value).expanduser().resolve(strict=False)


def _validated_timeout(value: float) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
        raise DetachedRealAdmissionChildLaunchRefused("timeout_seconds must be positive")
    return float(value)


def _launch_detached_real_admission_invocation(
    invocation: DetachedRealAdmissionChildInvocation,
    *,
    stdout_path: str | Path,
    stderr_path: str | Path,
) -> DetachedRealAdmissionChildProcess:
    stdout = _validated_output_path(stdout_path, "stdout_path")
    stderr = _validated_output_path(stderr_path, "stderr_path")
    if stdout == stderr:
        raise DetachedRealAdmissionChildLaunchRefused("stdout_path and stderr_path must be distinct")
    try:
        stdout.parent.mkdir(parents=True, exist_ok=True)
        stderr.parent.mkdir(parents=True, exist_ok=True)
        with stdout.open("xb") as stdout_stream, stderr.open("xb") as stderr_stream:
            process = subprocess.Popen(
                [str(invocation.executable), *invocation.arguments],
                executable=str(invocation.executable),
                cwd=str(invocation.repository_root),
                stdin=subprocess.DEVNULL,
                stdout=stdout_stream,
                stderr=stderr_stream,
                creationflags=invocation.creationflags,
            )
    except OSError as exc:
        raise DetachedRealAdmissionChildLaunchError(
            _diagnostic(invocation.executable, invocation.repository_root, exc)
        ) from exc
    return DetachedRealAdmissionChildProcess(
        process=process,
        invocation=invocation,
        stdout_path=stdout,
        stderr_path=stderr,
    )


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


def _read_import_probe_result(
    path: Path,
    *,
    invocation: DetachedRealAdmissionChildInvocation,
) -> DetachedRealAdmissionImportProbeResult:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DetachedRealAdmissionChildLaunchError(
            DetachedRealAdmissionChildLaunchDiagnostic(
                executable=str(invocation.executable),
                cwd=str(invocation.repository_root),
                exception_type=type(exc).__name__,
                exception_message=str(exc),
            )
        ) from exc
    required = {
        "contract", "version", "passed", "cwd", "executable", "sys_path_0",
        "entry_invocation_mode", "entrypoint_module", "repository_module_identity",
        "exception_type", "exception_message",
    }
    if not isinstance(value, dict) or set(value) != required:
        raise DetachedRealAdmissionChildLaunchRefused("import probe result shape is invalid")
    if value["contract"] != IMPORT_PROBE_CONTRACT or value["version"] != IMPORT_PROBE_VERSION:
        raise DetachedRealAdmissionChildLaunchRefused("import probe result contract is unsupported")
    result = DetachedRealAdmissionImportProbeResult(
        passed=value["passed"],
        cwd=value["cwd"],
        executable=value["executable"],
        sys_path_0=value["sys_path_0"],
        entry_invocation_mode=value["entry_invocation_mode"],
        entrypoint_module=value["entrypoint_module"],
        repository_module_identity=value["repository_module_identity"],
        exception_type=value["exception_type"],
        exception_message=value["exception_message"],
        invocation=invocation,
    )
    if result.cwd != str(invocation.repository_root):
        raise DetachedRealAdmissionChildLaunchRefused("import probe did not preserve the explicit repository cwd")
    if result.executable != str(invocation.executable):
        raise DetachedRealAdmissionChildLaunchRefused("import probe did not preserve the explicit executable")
    if result.entry_invocation_mode != "PYTHON_MODULE":
        raise DetachedRealAdmissionChildLaunchRefused("import probe did not use python module invocation mode")
    if result.entrypoint_module != invocation.entrypoint_module:
        raise DetachedRealAdmissionChildLaunchRefused("import probe entrypoint module does not match the real child")
    return result


__all__ = [
    "DetachedRealAdmissionChildLaunchDiagnostic",
    "DetachedRealAdmissionChildLaunchError",
    "DetachedRealAdmissionChildLaunchRefused",
    "DetachedRealAdmissionChildInvocation",
    "DetachedRealAdmissionChildProcess",
    "DetachedRealAdmissionImportProbeResult",
    "build_detached_real_admission_child_invocation",
    "detached_real_admission_creationflags",
    "launch_detached_real_admission_child",
    "launch_detached_real_admission_external_script_child",
    "run_detached_real_admission_import_probe",
]
