"""tests/test_geometric_harvester_readonly_purity_characterization.py

Tests-only / source-AST characterization lock: ``torment_service/geometric_harvester.py``
remains a READ-ONLY, NON-AUTHORING input bridge for substrate-independent shaping.

The harvester's own docstring asserts it is a "read-only bridge ... does not modify
kernel, character, or SRG state." Nothing structurally enforced that. This file pins it.

CHARACTERIZATION, not a safety proof. It changes no production behaviour and imports
no production module (the source is parsed, never imported), so it has no runtime side
effects. No endpoint/API/schema, prompt mutation/exposure, output/review/control,
writer/memory/persistence, Gate A / Gate D, database/substrate, or audit-owner movement.

Non-duplication (deliberate):
  The forbidden WRITE / PERSISTENCE / MEMORY-GRAPH / PROMOTION direct-call absence for
  ``geometric_harvester.py`` is ALREADY owned by C1 in
  ``tests/test_gate_a_tests_only_locks_c1_c5.py`` (its ``FORBIDDEN_CALL_NAMES`` +
  ``.write(...)`` + write-mode ``open(...)``, parametrised over the advisory modules).
  This file does NOT re-assert that set. It locks the COMPLEMENTARY invariants that C1
  leaves unguarded:
    1. Closed import surface — only ``__future__``, ``typing``, ``.thinking_models``.
    2. Absence of retrieval / prompt / model / agent-loop call surfaces (the names C1
       omits), so the read-only bridge cannot reach into cognition/output/control.
    3. No mutation of input objects — no subscript/attribute assignment targets and no
       mutating method calls (``.append`` / ``.update`` / ``.setdefault`` / ...).
    4. Return-only extractor shape — ``harvest_geometric_context`` returns ``None`` or
       constructs ``GeometricStanceContext``, and never returns a source/input object.

Each matcher carries a "has teeth" self-test so a green run over the real module is
meaningful.
"""
from __future__ import annotations

import ast
import unittest
from pathlib import Path

# Project root (torment_fabric/) -> torment_service/.
_SERVICE_DIR = Path(__file__).resolve().parents[1] / "torment_service"
_MODULE = "geometric_harvester.py"
_TARGET_FUNC = "harvest_geometric_context"

# Import surface allowed for a read-only shaping bridge (resolved `from M import ...`
# module name; relative `.thinking_models` resolves to "thinking_models").
_ALLOWED_IMPORT_MODULES = frozenset({"__future__", "typing", "thinking_models"})

# Retrieval / prompt / model / agent-loop call names that C1 does NOT cover. A read-only
# bridge must not reach these surfaces. (Write/persistence/memory/promotion call names
# are locked by C1 and intentionally not duplicated here.)
_FORBIDDEN_BRIDGE_CALL_NAMES = frozenset({
    "query",
    "assemble_context",
    "run_turn",
    "complete",
    "review",
    "_execute",
    "_complete_llm_prompt_request",
    "observe_prompt_inclusion_packet",
})

# Method names whose call mutates a (possibly input) object.
_MUTATING_METHOD_NAMES = frozenset({
    "append", "extend", "insert", "update", "setdefault", "pop", "popitem",
    "clear", "remove", "add", "discard", "__setitem__", "sort", "writelines",
})


def _parse(filename: str) -> ast.AST:
    """Parse a torment_service source file. Source-only; never imported."""
    path = _SERVICE_DIR / filename
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _called_name(call_node: ast.Call):
    """Resolved callee identifier: attr for ``x.y.name(...)``, id for ``name(...)``."""
    func = call_node.func
    if isinstance(func, ast.Attribute):
        return func.attr
    if isinstance(func, ast.Name):
        return func.id
    return None


def _find_function(tree: ast.AST, name: str):
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    return None


class TestGeometricHarvesterImportSurface(unittest.TestCase):
    def test_only_allowed_imports(self):
        tree = _parse(_MODULE)
        bare_imports = [n for n in ast.walk(tree) if isinstance(n, ast.Import)]
        self.assertEqual(
            bare_imports, [],
            "geometric_harvester.py must use no bare `import X` statements",
        )
        offenders = [
            (n.lineno, n.module)
            for n in ast.walk(tree)
            if isinstance(n, ast.ImportFrom)
            and (n.module or "") not in _ALLOWED_IMPORT_MODULES
        ]
        self.assertEqual(
            offenders, [],
            "geometric_harvester.py import surface must be "
            f"{sorted(_ALLOWED_IMPORT_MODULES)}; unexpected import(s): {offenders!r}",
        )

    def test_import_matcher_has_teeth(self):
        # A forbidden production import IS detected by the same predicate.
        tree = ast.parse("from .fabric import TormentFabric\n")
        offenders = [
            n.module for n in ast.walk(tree)
            if isinstance(n, ast.ImportFrom)
            and (n.module or "") not in _ALLOWED_IMPORT_MODULES
        ]
        self.assertIn("fabric", offenders)


class TestGeometricHarvesterNoBridgeCalls(unittest.TestCase):
    def test_no_retrieval_prompt_model_or_loop_calls(self):
        tree = _parse(_MODULE)
        violations = [
            (getattr(n, "lineno", -1), _called_name(n))
            for n in ast.walk(tree)
            if isinstance(n, ast.Call) and _called_name(n) in _FORBIDDEN_BRIDGE_CALL_NAMES
        ]
        self.assertEqual(
            violations, [],
            "geometric_harvester.py must not call retrieval/prompt/model/loop "
            f"surfaces: {violations!r}",
        )

    def test_bridge_call_matcher_has_teeth(self):
        tree = ast.parse("def f(x):\n    return x.run_turn()\n")
        hits = {
            _called_name(n) for n in ast.walk(tree)
            if isinstance(n, ast.Call) and _called_name(n) in _FORBIDDEN_BRIDGE_CALL_NAMES
        }
        self.assertIn("run_turn", hits)


class TestGeometricHarvesterNoMutation(unittest.TestCase):
    def test_no_subscript_or_attribute_assignment_targets(self):
        tree = _parse(_MODULE)
        bad = []
        for n in ast.walk(tree):
            if isinstance(n, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
                targets = n.targets if isinstance(n, ast.Assign) else [n.target]
                for t in targets:
                    if isinstance(t, (ast.Subscript, ast.Attribute)):
                        bad.append((getattr(n, "lineno", -1), type(t).__name__))
        self.assertEqual(
            bad, [],
            "geometric_harvester.py must not assign into subscripts/attributes "
            f"(would mutate inputs/shared state): {bad!r}",
        )

    def test_no_mutating_method_calls(self):
        tree = _parse(_MODULE)
        violations = [
            (getattr(n, "lineno", -1), _called_name(n))
            for n in ast.walk(tree)
            if isinstance(n, ast.Call) and _called_name(n) in _MUTATING_METHOD_NAMES
        ]
        self.assertEqual(
            violations, [],
            f"geometric_harvester.py must call no mutating methods: {violations!r}",
        )

    def test_mutation_matcher_has_teeth(self):
        tree = ast.parse("def f(d):\n    d.update({'x': 1})\n    d['y'] = 2\n")
        method_hits = {
            _called_name(n) for n in ast.walk(tree)
            if isinstance(n, ast.Call) and _called_name(n) in _MUTATING_METHOD_NAMES
        }
        subscript_targets = [
            t for n in ast.walk(tree) if isinstance(n, ast.Assign)
            for t in n.targets if isinstance(t, ast.Subscript)
        ]
        self.assertIn("update", method_hits)
        self.assertTrue(subscript_targets)


class TestGeometricHarvesterReturnShape(unittest.TestCase):
    def test_returns_only_none_or_geometric_stance_context(self):
        func = _find_function(_parse(_MODULE), _TARGET_FUNC)
        self.assertIsNotNone(func, f"{_TARGET_FUNC} not found")
        returns = [n for n in ast.walk(func) if isinstance(n, ast.Return)]
        self.assertTrue(returns, "harvest_geometric_context has no return statements")
        for r in returns:
            v = r.value
            is_none = isinstance(v, ast.Constant) and v.value is None
            is_ctx = isinstance(v, ast.Call) and _called_name(v) == "GeometricStanceContext"
            self.assertTrue(
                is_none or is_ctx,
                f"return at line {getattr(r, 'lineno', -1)} must be None or "
                "GeometricStanceContext(...)",
            )

    def test_does_not_return_a_source_or_input_object(self):
        func = _find_function(_parse(_MODULE), _TARGET_FUNC)
        param_names = (
            {a.arg for a in func.args.args}
            | {a.arg for a in func.args.kwonlyargs}
            | {a.arg for a in getattr(func.args, "posonlyargs", [])}
        )
        bad = [
            getattr(n, "lineno", -1) for n in ast.walk(func)
            if isinstance(n, ast.Return)
            and isinstance(n.value, ast.Name)
            and n.value.id in param_names
        ]
        self.assertEqual(
            bad, [],
            f"harvest_geometric_context must not return a source/input object: {bad!r}",
        )


if __name__ == "__main__":
    unittest.main()
