"""Phase-1 import-boundary tests for the production Brainvision package."""

from __future__ import annotations

import ast
import json
from pathlib import Path
import subprocess
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPOSITORY_ROOT / "brainvision"


def _assert_inert_module_source(path: Path) -> None:
    """Allow only a module docstring and an empty ``__all__`` declaration."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    assert len(tree.body) == 2

    docstring, exports = tree.body
    assert isinstance(docstring, ast.Expr)
    assert isinstance(docstring.value, ast.Constant)
    assert isinstance(docstring.value.value, str)

    assert isinstance(exports, ast.Assign)
    assert len(exports.targets) == 1
    assert isinstance(exports.targets[0], ast.Name)
    assert exports.targets[0].id == "__all__"
    assert isinstance(exports.value, ast.Tuple)
    assert exports.value.elts == []


def test_phase1_modules_have_no_runtime_declarations() -> None:
    """Phase 1 contains no DTO, engine, state, registry, or integration code."""
    _assert_inert_module_source(PACKAGE_ROOT / "__init__.py")
    _assert_inert_module_source(PACKAGE_ROOT / "protocols.py")


def test_phase1_imports_are_isolated_and_inert() -> None:
    """A clean interpreter imports only the two inert production modules."""
    code = """
import json
import sys

before = set(sys.modules)
import brainvision
after_package = set(sys.modules)
import brainvision.protocols
after_protocols = set(sys.modules)

print(json.dumps({
    "package_all": list(brainvision.__all__),
    "protocols_all": list(brainvision.protocols.__all__),
    "package_added": sorted(after_package - before),
    "protocols_added": sorted(after_protocols - after_package),
    "loaded_modules": sorted(after_protocols - before),
}))
"""
    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    observed = json.loads(completed.stdout)

    assert observed["package_all"] == []
    assert observed["protocols_all"] == []
    assert observed["package_added"] == ["brainvision"]
    assert observed["protocols_added"] == ["brainvision.protocols"]
    assert observed["loaded_modules"] == ["brainvision", "brainvision.protocols"]
