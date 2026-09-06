"""Fresh-interpreter regression coverage for the P3 corrective-freeze boundary."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


_REPOSITORY = Path(__file__).resolve().parents[1]
_ENTRYPOINT = "torment_service.substrate.detached_real_admission_child_entrypoint"


def _cold_python(code: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=_REPOSITORY,
        env=os.environ.copy(),
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.parametrize(
    "imports",
    (
        (
            "import torment_service.substrate.corrective_freeze_packet\n"
            "import torment_service.substrate.migration.root_p3_source_admission\n"
            "import torment_service.substrate.offline_cutover_controller\n"
        ),
        (
            "import torment_service.substrate.migration.root_p3_source_admission\n"
            "import torment_service.substrate.corrective_freeze_packet\n"
            "import torment_service.substrate.offline_cutover_controller\n"
        ),
        "import torment_service.substrate.offline_cutover_controller\n",
        (
            "from torment_service.substrate.migration import (\n"
            "    NativeRootP3SourceAdmissionService, RootP3SourceAdmissionRequest,\n"
            ")\n"
        ),
    ),
    ids=("corrective-first", "p3-first", "controller-first", "migration-package-surface"),
)
def test_p3_corrective_freeze_import_boundary_is_cold_start_safe(imports: str) -> None:
    completed = _cold_python(imports)

    assert completed.returncode == 0, completed.stderr


def test_p3_exact_module_import_probe_is_cold_start_safe(tmp_path: Path) -> None:
    result_path = tmp_path / "exact-module-import-probe.json"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            _ENTRYPOINT,
            "--import-probe-only",
            "--result-path",
            str(result_path),
        ],
        cwd=_REPOSITORY,
        env=os.environ.copy(),
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    result = json.loads(result_path.read_text(encoding="utf-8"))
    assert result["passed"] is True
    assert result["cwd"] == str(_REPOSITORY)
    assert result["executable"] == str(Path(sys.executable).resolve())
    assert result["entry_invocation_mode"] == "PYTHON_MODULE"
    assert result["entrypoint_module"] == _ENTRYPOINT
