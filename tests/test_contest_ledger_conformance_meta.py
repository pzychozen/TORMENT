"""tests/test_contest_ledger_conformance_meta.py

Mandatory B2-S3 conformance guards for the Track B v0.2 ContestLedger.

Guard 1 (key requirement): no ordinary production module under
``torment_service/`` imports ``torment_service.contest_ledger``. The runtime
must not consume it. AST-based — not text/substring matching. Tests may
import it.

Guard 2 (import purity): ``contest_ledger.py`` imports nothing from the
runtime authority/consumer surfaces (memory_graph, fabric, spine, governance,
retrieval, cognition, MCP/API, app). This is how the slice's "no row
mutation / no target lookup / no resolver / no consumer wiring" posture is
enforced structurally rather than by synthetic runtime fixtures.

Only ``torment_service/**/*.py`` is scanned. Docs and tests are not scanned.
"""
from __future__ import annotations

import ast
from pathlib import Path

_TESTS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _TESTS_DIR.parent
_SERVICE_DIR = _REPO_ROOT / "torment_service"
_LEDGER_MODULE = (_SERVICE_DIR / "contest_ledger.py").resolve()

# Forbidden import segments for contest_ledger.py — runtime authority and
# consumer surfaces the persistence slice must never touch. (Path helpers
# ``embedding_store`` / ``pathing`` and the B2-S2 ``contest_record`` are
# deliberately NOT in this set.)
_FORBIDDEN_IMPORT_SEGMENTS = {
    "memory_graph", "fabric", "spine", "governance",
    "retrieval_assembler", "retrieval", "cognition", "mcp_server", "app",
}


def _iter_service_py_files():
    for path in sorted(_SERVICE_DIR.rglob("*.py")):
        if path.resolve() == _LEDGER_MODULE:
            continue
        yield path


def _imports_contest_ledger(tree: ast.AST) -> bool:
    """True iff the AST imports the contest_ledger module.

    Covers:
        import torment_service.contest_ledger
        from torment_service import contest_ledger
        from torment_service.contest_ledger import X
        from .contest_ledger import X
        from . import contest_ledger
    """
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name or ""
                if name == "contest_ledger" or name.endswith(".contest_ledger"):
                    return True
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if mod == "contest_ledger" or mod.endswith(".contest_ledger"):
                return True
            for alias in node.names:
                if alias.name == "contest_ledger":
                    return True
    return False


def _imported_module_segments(tree: ast.AST):
    """Yield each dotted-path segment of every module the tree imports."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                for seg in (alias.name or "").split("."):
                    if seg:
                        yield seg
        elif isinstance(node, ast.ImportFrom):
            for seg in (node.module or "").split("."):
                if seg:
                    yield seg
            # `from . import contest_ledger` / `from . import fabric`
            if (node.module or "") == "":
                for alias in node.names:
                    if alias.name:
                        yield alias.name


def test_ledger_module_exists():
    assert _LEDGER_MODULE.exists(), f"missing module: {_LEDGER_MODULE}"


def test_no_production_module_imports_contest_ledger():
    offenders = []
    for path in _iter_service_py_files():
        source = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError:
            continue
        if _imports_contest_ledger(tree):
            offenders.append(str(path.relative_to(_REPO_ROOT)))
    assert not offenders, (
        "contest_ledger must remain importer-free in production; "
        f"imported by: {offenders}"
    )


def test_contest_ledger_imports_no_authority_or_consumer_surface():
    tree = ast.parse(
        _LEDGER_MODULE.read_text(encoding="utf-8"), filename=str(_LEDGER_MODULE)
    )
    hits = sorted(
        seg for seg in _imported_module_segments(tree)
        if seg in _FORBIDDEN_IMPORT_SEGMENTS
    )
    assert not hits, (
        "contest_ledger.py must not import runtime authority/consumer "
        f"surfaces; found forbidden import segments: {hits}"
    )
