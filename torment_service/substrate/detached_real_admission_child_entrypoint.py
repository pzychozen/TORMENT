"""Repository-owned detached admission child entrypoint.

This module establishes the repository import context with ``python -m``.
It provides only an import-only probe and an explicit external-script bridge;
it owns no real-root, writer, SQLite, P1, or admission authority.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
from pathlib import Path
import runpy
import sys
from typing import Sequence
from uuid import uuid4


ENTRYPOINT_MODULE = "torment_service.substrate.detached_real_admission_child_entrypoint"
IMPORT_PROBE_CONTRACT = "TORMENT_DETACHED_REAL_ADMISSION_EXACT_MODE_IMPORT_PROBE"
IMPORT_PROBE_VERSION = 1
_REQUIRED_IMPORTS = (
    "torment_service",
    "torment_service.substrate.real_root_typed_evidence",
    "torment_service.substrate.writer_freeze_evidence",
    "torment_service.substrate.file_backed_real_admission_administration_runner",
)


def _import_required_modules() -> str:
    """Import the bounded admission plumbing dependencies without data access."""

    imported = {name: importlib.import_module(name) for name in _REQUIRED_IMPORTS}
    package_file = getattr(imported["torment_service"], "__file__", None)
    if not isinstance(package_file, str) or not package_file:
        raise RuntimeError("torment_service did not expose a repository module identity")
    return str(Path(package_file).resolve())


def _atomic_json(path: Path, value: dict[str, object]) -> None:
    """Write a complete probe result before atomically replacing its sibling."""

    path = path.expanduser().resolve(strict=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(value, ensure_ascii=True, allow_nan=False, separators=(",", ":"), sort_keys=True))
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _import_probe_result() -> dict[str, object]:
    result: dict[str, object] = {
        "contract": IMPORT_PROBE_CONTRACT,
        "version": IMPORT_PROBE_VERSION,
        "passed": False,
        "cwd": str(Path.cwd().resolve()),
        "executable": sys.executable,
        "sys_path_0": sys.path[0] if sys.path else "",
        "entry_invocation_mode": "PYTHON_MODULE",
        "entrypoint_module": ENTRYPOINT_MODULE,
        "repository_module_identity": None,
        "exception_type": None,
        "exception_message": None,
    }
    try:
        result["repository_module_identity"] = _import_required_modules()
    except BaseException as exc:
        result["exception_type"] = type(exc).__name__
        result["exception_message"] = str(exc)
    else:
        result["passed"] = True
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Repository-owned detached real-admission child entrypoint."
    )
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--import-probe-only", action="store_true")
    modes.add_argument("--execute-external-script", metavar="PATH")
    parser.add_argument("--result-path", metavar="PATH")
    parser.add_argument("external_script_arguments", nargs=argparse.REMAINDER)
    return parser


def _execute_external_script(script_text: str, arguments: Sequence[str]) -> int:
    """Run a caller-owned script only after repository imports have passed."""

    script = Path(script_text).expanduser().resolve(strict=False)
    if not script.is_file():
        raise FileNotFoundError(f"explicit external administration script does not exist: {script}")
    _import_required_modules()
    script_arguments = list(arguments)
    if script_arguments[:1] == ["--"]:
        script_arguments.pop(0)
    prior_argv = sys.argv
    try:
        sys.argv = [str(script), *script_arguments]
        runpy.run_path(str(script), run_name="__main__")
    finally:
        sys.argv = prior_argv
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    if arguments.import_probe_only:
        if arguments.result_path is None:
            _parser().error("--import-probe-only requires --result-path")
        if arguments.external_script_arguments:
            _parser().error("--import-probe-only does not accept external-script arguments")
        result = _import_probe_result()
        _atomic_json(Path(arguments.result_path), result)
        return 0 if result["passed"] else 1
    if arguments.result_path is not None:
        _parser().error("--result-path is valid only with --import-probe-only")
    return _execute_external_script(
        arguments.execute_external_script,
        arguments.external_script_arguments,
    )


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["ENTRYPOINT_MODULE", "IMPORT_PROBE_CONTRACT", "IMPORT_PROBE_VERSION", "main"]
