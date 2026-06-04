"""tests/test_contest_record_conformance_meta.py

Mandatory B2-S2 conformance guards for the Track B v0.2 ContestRecord
Slice-0. These make the "NOT load-bearing" commitment executable, mirroring
the lifecycle Slice-0 posture.

Guard 1 (the key requirement): no production module under ``torment_service/``
imports ``torment_service.contest_record``. The runtime must not know about
it. AST-based — not text/substring matching.

Guard 2: ``contest_record.py`` itself performs no filesystem / path-
construction behavior (no os/io/pathlib/etc. imports, no ``open()`` call).
AST-based.

Only ``torment_service/**/*.py`` is scanned. Docs and tests are not scanned.
"""
from __future__ import annotations

import ast
from pathlib import Path

# tests/ is a sibling of torment_service/ inside torment_fabric/.
_TESTS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _TESTS_DIR.parent
_SERVICE_DIR = _REPO_ROOT / "torment_service"
_CONTEST_MODULE = (_SERVICE_DIR / "contest_record.py").resolve()

# Filesystem / path-construction modules that the pure Slice-0 module must
# not pull in. ``json`` is intentionally absent — it is not a filesystem
# dependency and serialization here returns dicts (callers do the I/O).
_FS_MODULE_ROOTS = {
    "os", "io", "pathlib", "shutil", "tempfile", "glob", "fileinput",
}


def _iter_service_py_files():
    for path in sorted(_SERVICE_DIR.rglob("*.py")):
        if path.resolve() == _CONTEST_MODULE:
            continue
        yield path


def _imports_contest_record(tree: ast.AST) -> bool:
    """True iff the AST contains any import of the contest_record module.

    Covers:
        import torment_service.contest_record
        import <pkg>.contest_record
        from torment_service import contest_record
        from . import contest_record
        from torment_service.contest_record import X
        from .contest_record import X
    """
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name or ""
                if name == "contest_record" or name.endswith(".contest_record"):
                    return True
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if mod == "contest_record" or mod.endswith(".contest_record"):
                return True
            for alias in node.names:
                if alias.name == "contest_record":
                    return True
    return False


def test_contest_module_exists():
    assert _CONTEST_MODULE.exists(), f"missing module: {_CONTEST_MODULE}"


def test_no_production_module_imports_contest_record():
    offenders = []
    for path in _iter_service_py_files():
        source = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError:
            # A file that does not parse cannot import our module; skip it.
            continue
        if _imports_contest_record(tree):
            offenders.append(str(path.relative_to(_REPO_ROOT)))
    assert not offenders, (
        "contest_record must remain importer-free in production; "
        f"imported by: {offenders}"
    )


def test_contest_record_has_no_filesystem_behavior():
    tree = ast.parse(
        _CONTEST_MODULE.read_text(encoding="utf-8"), filename=str(_CONTEST_MODULE)
    )
    findings = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = (alias.name or "").split(".")[0]
                if root in _FS_MODULE_ROOTS:
                    findings.append(f"import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            if root in _FS_MODULE_ROOTS:
                findings.append(f"from {node.module} import ...")
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id == "open":
                findings.append("call to open()")
    assert not findings, (
        f"contest_record.py must perform no filesystem behavior; found: {findings}"
    )
