"""tests/test_regime_b_dream_absence_characterization.py

Regime-B / Dream readiness guard — tests-only, source/AST characterization.

This pins the CURRENT closed state of Dream / Incubation / Regime-B: doctrine
exists (Document B defines Dream / Incubation / Regime B at requirement level),
but there is NO runtime. It proves, by source + AST scan (no production import,
no execution), that the production package `torment_service/` contains:

  * no dream / incubation / chamber / Regime-B runtime module or class/def
    entrypoint;
  * no scheduler library, no asyncio background-task creation, and no
    dream/Regime-B-scoped background thread or `while True` loop;
  * no dream wiring in the entrypoints (`app.py` / `spine.py` / `agent_loop.py`
    / `mcp_server.py`) — no dream symbol, dream import, or dream route.

It also asserts the positive doctrine anchors (Document B + the status board),
and includes a teeth test proving the matcher flags an obvious synthetic dream
runtime — so the guard is NOT vacuous.

Scope: tests-only. This file OPENS NOTHING. It builds no dream runtime,
scheduler, trigger, budget, loop, chamber store, Gate D / Envelope-Audit
runtime, model/provider path, persistence, or wiring; it only asserts their
absence. Allowances (per Document B and the current codebase):
  * `threading.Lock` / `RLock` are mutual-exclusion primitives, NOT schedulers;
  * the existing benign `threading.Thread` repair-job runner in `fabric.py` is
    not dream/Regime-B and is not flagged (the thread guard is dream-scoped);
  * `agent_loop.enter_reflex` (drift/kernel-triggered stabilization) is not
    dream/incubation; `"scheduled"` as an external source_type label is not an
    internal scheduler;
  * docs and audit-module docstrings may MENTION dream / Gate D as
    negative-boundary exclusions — those are not runtime.
"""
from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_SERVICE_DIR = _REPO / "torment_service"
_DOCS_DIR = _REPO / "docs"

# Dream / Incubation / private-chamber / Regime-B tokens. "regime[_ ]?b" is
# deliberately narrow so ordinary "regime" usages (DriftRegime, high_regime_*)
# do NOT match — only Regime-B.
_DREAM_RE = re.compile(r"dream|incubat|chamber|regime[_ ]?b", re.I)

_SCHEDULER_LIB_ROOTS = {"apscheduler", "schedule", "sched", "celery", "crontab", "croniter"}
_ASYNCIO_BG_ATTRS = {"create_task", "ensure_future", "run_forever", "new_event_loop", "get_event_loop"}
_ENTRYPOINTS = ("app.py", "spine.py", "agent_loop.py", "mcp_server.py")


def _read(path: Path) -> str:
    # utf-8-sig tolerates the BOM some kernel/*.py files carry.
    return path.read_text(encoding="utf-8-sig")


def _prod_files():
    return sorted(p for p in _SERVICE_DIR.rglob("*.py"))


def _prod_trees():
    out = []
    for p in _prod_files():
        out.append((p, ast.parse(_read(p), filename=p.name)))
    return out


# --- reusable detectors (shared by the production scan and the teeth test) ---

def _dream_named_defs(tree: ast.AST):
    return sorted(
        n.name for n in ast.walk(tree)
        if isinstance(n, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
        and _DREAM_RE.search(n.name)
    )


def _scheduler_lib_imports(tree: ast.AST):
    roots = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            roots.update(a.name.split(".")[0] for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module:
            roots.add(n.module.split(".")[0])
    return sorted(roots & _SCHEDULER_LIB_ROOTS)


def _asyncio_bg_calls(tree: ast.AST):
    hits = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute):
            f = n.func
            if f.attr in _ASYNCIO_BG_ATTRS and isinstance(f.value, ast.Name) and f.value.id == "asyncio":
                hits.append((getattr(n, "lineno", -1), f.attr))
    return hits


def _dream_import_modules(tree: ast.AST):
    mods = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            mods += [a.name for a in n.names if _DREAM_RE.search(a.name)]
        elif isinstance(n, ast.ImportFrom) and n.module and _DREAM_RE.search(n.module):
            mods.append(n.module)
    return mods


def _dream_route_strings(tree: ast.AST):
    # String constants that look like URL routes and name a dream token.
    return sorted(
        n.value for n in ast.walk(tree)
        if isinstance(n, ast.Constant) and isinstance(n.value, str)
        and n.value.startswith("/") and _DREAM_RE.search(n.value)
    )


def _enclosing_func_names(tree: ast.AST):
    """Map each node to the name of its nearest enclosing function (or '')."""
    parent_func = {}
    def visit(node, cur):
        for child in ast.iter_child_nodes(node):
            nxt = child.name if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) else cur
            parent_func[child] = cur
            visit(child, nxt)
    visit(tree, "")
    return parent_func


def _target_name(call: ast.Call) -> str:
    for kw in call.keywords:
        if kw.arg == "target":
            v = kw.value
            if isinstance(v, ast.Attribute):
                return v.attr
            if isinstance(v, ast.Name):
                return v.id
    return ""


def _dream_scoped_thread_sites(tree: ast.AST, file_stem: str):
    """threading.Thread(...) / Thread(...) sites that are dream-scoped: enclosing
    function, file stem, or thread target references a dream token."""
    encl = _enclosing_func_names(tree)
    hits = []
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call):
            continue
        f = n.func
        is_thread = (isinstance(f, ast.Attribute) and f.attr == "Thread") or (
            isinstance(f, ast.Name) and f.id == "Thread"
        )
        if not is_thread:
            continue
        ctx = " ".join([encl.get(n, ""), file_stem, _target_name(n)])
        if _DREAM_RE.search(ctx):
            hits.append((getattr(n, "lineno", -1), ctx.strip()))
    return hits


def _dream_scoped_while_true(tree: ast.AST, file_stem: str):
    """`while True:` loops that are dream-scoped (enclosing func or file stem)."""
    encl = _enclosing_func_names(tree)
    hits = []
    for n in ast.walk(tree):
        if isinstance(n, ast.While) and isinstance(n.test, ast.Constant) and n.test.value is True:
            ctx = " ".join([encl.get(n, ""), file_stem])
            if _DREAM_RE.search(ctx):
                hits.append(getattr(n, "lineno", -1))
    return hits


# ---------------------------------------------------------------------------
# 1. No dream/incubation/chamber/Regime-B runtime module or entrypoint
# ---------------------------------------------------------------------------

class TestNoDreamRuntimeModuleOrEntrypoint(unittest.TestCase):
    def test_no_production_file_named_for_dream(self):
        offenders = [str(p.relative_to(_REPO)) for p in _prod_files() if _DREAM_RE.search(p.stem)]
        self.assertEqual(offenders, [], f"dream/Regime-B-named production module(s): {offenders!r}")

    def test_no_production_class_or_def_named_for_dream(self):
        offenders = {}
        for p, tree in _prod_trees():
            names = _dream_named_defs(tree)
            if names:
                offenders[str(p.relative_to(_REPO))] = names
        self.assertEqual(offenders, {}, f"dream/Regime-B-named class/def in production: {offenders!r}")


# ---------------------------------------------------------------------------
# 2. No scheduler / background loop / self-trigger machinery
# ---------------------------------------------------------------------------

class TestNoSchedulerOrBackgroundLoop(unittest.TestCase):
    def test_no_scheduler_library_imported(self):
        offenders = {}
        for p, tree in _prod_trees():
            libs = _scheduler_lib_imports(tree)
            if libs:
                offenders[str(p.relative_to(_REPO))] = libs
        self.assertEqual(offenders, {}, f"scheduler library import(s) in production: {offenders!r}")

    def test_no_asyncio_background_task_creation(self):
        offenders = {}
        for p, tree in _prod_trees():
            calls = _asyncio_bg_calls(tree)
            if calls:
                offenders[str(p.relative_to(_REPO))] = calls
        self.assertEqual(offenders, {}, f"asyncio background-task creation in production: {offenders!r}")

    def test_no_dream_scoped_background_thread(self):
        # threading.Lock/RLock are fine; the existing fabric.py repair-job Thread
        # is non-dream and must not be flagged. Only dream-scoped threads fail.
        offenders = {}
        for p, tree in _prod_trees():
            sites = _dream_scoped_thread_sites(tree, p.stem)
            if sites:
                offenders[str(p.relative_to(_REPO))] = sites
        self.assertEqual(offenders, {}, f"dream/Regime-B-scoped background thread(s): {offenders!r}")

    def test_no_dream_scoped_while_true_loop(self):
        offenders = {}
        for p, tree in _prod_trees():
            sites = _dream_scoped_while_true(tree, p.stem)
            if sites:
                offenders[str(p.relative_to(_REPO))] = sites
        self.assertEqual(offenders, {}, f"dream/Regime-B-scoped while-True loop(s): {offenders!r}")


# ---------------------------------------------------------------------------
# 3. No dream wiring in the entrypoints
# ---------------------------------------------------------------------------

class TestNoDreamWiringInEntrypoints(unittest.TestCase):
    def _trees(self):
        return [(f, ast.parse(_read(_SERVICE_DIR / f), filename=f)) for f in _ENTRYPOINTS]

    def test_entrypoints_define_no_dream_symbol(self):
        offenders = {f: _dream_named_defs(t) for f, t in self._trees() if _dream_named_defs(t)}
        self.assertEqual(offenders, {}, f"dream symbol defined in entrypoint(s): {offenders!r}")

    def test_entrypoints_import_no_dream_module(self):
        offenders = {f: _dream_import_modules(t) for f, t in self._trees() if _dream_import_modules(t)}
        self.assertEqual(offenders, {}, f"dream module imported by entrypoint(s): {offenders!r}")

    def test_entrypoints_register_no_dream_route(self):
        offenders = {f: _dream_route_strings(t) for f, t in self._trees() if _dream_route_strings(t)}
        self.assertEqual(offenders, {}, f"dream route registered in entrypoint(s): {offenders!r}")


# ---------------------------------------------------------------------------
# 4. Positive doctrine anchors (dream exists as requirement, not runtime)
# ---------------------------------------------------------------------------

class TestDoctrineAnchorsExist(unittest.TestCase):
    def test_document_b_defines_dream_incubation_regime_b(self):
        text = _read(_DOCS_DIR / "TORMENT_PRIVATE_COGNITION_UNIFIED_REFLECTION_BLUEPRINT_v0.1.md")
        self.assertIn("Regime B", text)
        self.assertRegex(text, r"Dream ?/ ?Incubation")

    def test_document_b_parks_scheduler_trigger_budget(self):
        text = _read(_DOCS_DIR / "TORMENT_PRIVATE_COGNITION_UNIFIED_REFLECTION_BLUEPRINT_v0.1.md")
        # §5 / §11: scheduler / trigger / budget / interruption mechanics parked.
        self.assertRegex(text, r"[Ss]cheduler.*trigger.*budget")
        self.assertIn("PARKED", text.upper())

    def test_status_board_marks_regime_b_deferred(self):
        text = _read(_DOCS_DIR / "TORMENT_PRE_DATABASE_LAYER_STATUS_BOARD_v0.1.md")
        self.assertIn("Dream / incubation / Regime-B", text)
        self.assertIn("DEFERRED", text)


# ---------------------------------------------------------------------------
# 5. Teeth — the matcher flags an obvious synthetic dream runtime
# ---------------------------------------------------------------------------

_TEETH_SNIPPET = '''
import apscheduler
import threading
import asyncio


class DreamIncubationRuntime:
    """A forbidden Regime-B dream runtime (synthetic; for the teeth test only)."""

    def run_regime_b_loop(self):
        while True:
            self._incubate()

    def start(self):
        t = threading.Thread(target=self.run_regime_b_loop, daemon=True)
        t.start()
        asyncio.create_task(self._chamber_scheduler())
'''


class TestMatcherHasTeeth(unittest.TestCase):
    def setUp(self):
        self.tree = ast.parse(_TEETH_SNIPPET)

    def test_flags_dream_named_defs(self):
        names = _dream_named_defs(self.tree)
        self.assertIn("DreamIncubationRuntime", names)
        self.assertIn("run_regime_b_loop", names)

    def test_flags_scheduler_library_import(self):
        self.assertIn("apscheduler", _scheduler_lib_imports(self.tree))

    def test_flags_asyncio_background_task(self):
        self.assertTrue(_asyncio_bg_calls(self.tree), "teeth: asyncio.create_task not flagged")

    def test_flags_dream_scoped_thread(self):
        self.assertTrue(
            _dream_scoped_thread_sites(self.tree, "harmless_stem"),
            "teeth: dream-target Thread not flagged",
        )

    def test_flags_dream_scoped_while_true(self):
        self.assertTrue(
            _dream_scoped_while_true(self.tree, "harmless_stem"),
            "teeth: while-True inside dream-named loop not flagged",
        )

    def test_benign_thread_not_flagged(self):
        # Symmetry guard: a non-dream repair-style Thread in a non-dream file is
        # NOT flagged (mirrors the real fabric.py repair-job runner).
        benign = ast.parse(
            "import threading\n"
            "def start_repair_job():\n"
            "    t = threading.Thread(target=_run, daemon=True)\n"
            "    t.start()\n"
        )
        self.assertEqual(_dream_scoped_thread_sites(benign, "fabric"), [])


if __name__ == "__main__":
    unittest.main()
