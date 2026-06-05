"""tests/test_counter_contest_event_conformance_meta.py

Mandatory B2-S4 conformance guards for the Track B v0.2 CounterContestEvent
vocabulary. These make the "NOT load-bearing" commitment executable, mirroring
the B2-S2 ContestRecord posture.

Guard 1 (the key requirement): no production module under ``torment_service/``
imports ``torment_service.counter_contest_event`` — with a single explicit
path allowlist: ``torment_service/contest_event_ledger.py`` (the B2-S4 isolated
persistence module) is permitted to import it. Every other production module is
forbidden. The allowlist is an exact path set (no ``*_event`` prefix
exemption): any future importer requires an explicit guard edit and a new
ratified gate. AST-based — not text/substring matching.

Guard 2: ``counter_contest_event.py`` itself performs no filesystem / path-
construction behavior (no os/io/pathlib/etc. imports, no ``open()`` call).
AST-based.

Only ``torment_service/**/*.py`` is scanned. Docs and tests are not scanned.
"""
from __future__ import annotations

import ast
from pathlib import Path

_TESTS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _TESTS_DIR.parent
_SERVICE_DIR = _REPO_ROOT / "torment_service"
_EVENT_MODULE = (_SERVICE_DIR / "counter_contest_event.py").resolve()

# Explicit, exact-path allowlist of production modules permitted to import
# counter_contest_event. Exactly one entry: the B2-S4 isolated persistence
# ledger. NOT an *_event prefix exemption — a new importer requires editing
# this set (an intentional, reviewable guard change) plus a ratified gate.
_ALLOWED_EVENT_IMPORTERS = {
    (_SERVICE_DIR / "contest_event_ledger.py").resolve(),
}

# Filesystem / path-construction modules the pure vocabulary module must not
# pull in. ``json`` is intentionally absent — serialization returns dicts and
# callers do the I/O.
_FS_MODULE_ROOTS = {
    "os", "io", "pathlib", "shutil", "tempfile", "glob", "fileinput",
}


def _iter_service_py_files():
    for path in sorted(_SERVICE_DIR.rglob("*.py")):
        resolved = path.resolve()
        if resolved == _EVENT_MODULE:
            continue
        if resolved in _ALLOWED_EVENT_IMPORTERS:
            continue
        yield path


def _imports_counter_contest_event(tree: ast.AST) -> bool:
    """True iff the AST contains any import of the counter_contest_event module.

    Covers:
        import torment_service.counter_contest_event
        import <pkg>.counter_contest_event
        from torment_service import counter_contest_event
        from . import counter_contest_event
        from torment_service.counter_contest_event import X
        from .counter_contest_event import X
    """
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name or ""
                if name == "counter_contest_event" or name.endswith(".counter_contest_event"):
                    return True
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if mod == "counter_contest_event" or mod.endswith(".counter_contest_event"):
                return True
            for alias in node.names:
                if alias.name == "counter_contest_event":
                    return True
    return False


def test_event_module_exists():
    assert _EVENT_MODULE.exists(), f"missing module: {_EVENT_MODULE}"


def test_no_production_module_imports_counter_contest_event():
    offenders = []
    for path in _iter_service_py_files():
        source = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError:
            continue
        if _imports_counter_contest_event(tree):
            offenders.append(str(path.relative_to(_REPO_ROOT)))
    assert not offenders, (
        "counter_contest_event must remain importer-free in production "
        "(except the allowlisted event ledger); "
        f"imported by: {offenders}"
    )


def test_counter_contest_event_has_no_filesystem_behavior():
    tree = ast.parse(
        _EVENT_MODULE.read_text(encoding="utf-8"), filename=str(_EVENT_MODULE)
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
        "counter_contest_event.py must perform no filesystem behavior; "
        f"found: {findings}"
    )
