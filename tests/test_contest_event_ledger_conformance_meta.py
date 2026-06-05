"""tests/test_contest_event_ledger_conformance_meta.py

Mandatory B2-S4 conformance guards for the Track B v0.2 ContestEventLedger.

Guard 1 (key requirement): no ordinary production module under
``torment_service/`` imports ``torment_service.contest_event_ledger``. The
runtime must not consume it. AST-based — not text/substring matching. Tests may
import it.

Guard 2 (import purity): ``contest_event_ledger.py`` imports nothing from the
runtime authority/consumer surfaces (memory_graph, fabric, spine, governance,
retrieval, cognition, MCP/API, app). This is how the slice's "no row mutation /
no target lookup / no resolver / no consumer wiring" posture is enforced
structurally rather than by synthetic runtime fixtures.

Guard 3 (no resolver surface): ``contest_event_ledger.py`` defines none of the
resolver-/status-/ranking-shaped helper names. The ledger is literal and
observational; it must not grow an effective-state, latest-wins, count-as-
signal, or precedence surface. AST-based on the module's own def names.

Only ``torment_service/**/*.py`` is scanned. Docs and tests are not scanned.
"""
from __future__ import annotations

import ast
from pathlib import Path

_TESTS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _TESTS_DIR.parent
_SERVICE_DIR = _REPO_ROOT / "torment_service"
_LEDGER_MODULE = (_SERVICE_DIR / "contest_event_ledger.py").resolve()

# Forbidden import segments for contest_event_ledger.py — runtime authority and
# consumer surfaces the persistence slice must never touch. (Path helpers
# ``embedding_store`` / ``pathing`` and the B2-S4 ``counter_contest_event`` are
# deliberately NOT in this set.)
_FORBIDDEN_IMPORT_SEGMENTS = {
    "memory_graph", "fabric", "spine", "governance",
    "retrieval_assembler", "retrieval", "cognition", "mcp_server", "app",
}

# Resolver-/status-/ranking-shaped helper names that must never appear as
# definitions in the literal observational ledger surface. Equivalent names
# under different spellings are caught by review; this set locks the named
# Codex pressure points.
_FORBIDDEN_DEF_NAMES = {
    "get_latest_event", "get_effective_state", "get_effective_authority",
    "get_status", "is_active", "is_overturned", "resolve", "apply_events",
    "count_events_for_contest", "rank_by_contest_activity", "list_pending",
    "list_effective",
}


def _iter_service_py_files():
    for path in sorted(_SERVICE_DIR.rglob("*.py")):
        if path.resolve() == _LEDGER_MODULE:
            continue
        yield path


def _imports_contest_event_ledger(tree: ast.AST) -> bool:
    """True iff the AST imports the contest_event_ledger module."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name or ""
                if name == "contest_event_ledger" or name.endswith(".contest_event_ledger"):
                    return True
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if mod == "contest_event_ledger" or mod.endswith(".contest_event_ledger"):
                return True
            for alias in node.names:
                if alias.name == "contest_event_ledger":
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
            if (node.module or "") == "":
                for alias in node.names:
                    if alias.name:
                        yield alias.name


def _defined_names(tree: ast.AST):
    """Yield every function / method name defined in the tree."""
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            yield node.name


def test_ledger_module_exists():
    assert _LEDGER_MODULE.exists(), f"missing module: {_LEDGER_MODULE}"


def test_no_production_module_imports_contest_event_ledger():
    offenders = []
    for path in _iter_service_py_files():
        source = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError:
            continue
        if _imports_contest_event_ledger(tree):
            offenders.append(str(path.relative_to(_REPO_ROOT)))
    assert not offenders, (
        "contest_event_ledger must remain importer-free in production; "
        f"imported by: {offenders}"
    )


def test_contest_event_ledger_imports_no_authority_or_consumer_surface():
    tree = ast.parse(
        _LEDGER_MODULE.read_text(encoding="utf-8"), filename=str(_LEDGER_MODULE)
    )
    hits = sorted(
        seg for seg in _imported_module_segments(tree)
        if seg in _FORBIDDEN_IMPORT_SEGMENTS
    )
    assert not hits, (
        "contest_event_ledger.py must not import runtime authority/consumer "
        f"surfaces; found forbidden import segments: {hits}"
    )


def test_contest_event_ledger_defines_no_resolver_surface():
    tree = ast.parse(
        _LEDGER_MODULE.read_text(encoding="utf-8"), filename=str(_LEDGER_MODULE)
    )
    hits = sorted(set(_defined_names(tree)) & _FORBIDDEN_DEF_NAMES)
    assert not hits, (
        "contest_event_ledger.py must remain a literal observational ledger; "
        f"found forbidden resolver-/status-shaped def names: {hits}"
    )
