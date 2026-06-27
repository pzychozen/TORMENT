"""tests/test_thinking_controller_import_surface_characterization.py

Tests-only / source-AST characterization lock: ``torment_service/thinking_controller.py``
remains an ADVISORY-ONLY thinking router with a closed import surface.

The thinking-router decides retrieval shape (MemoryPlan top_k / weight by lane) and
advisory stance — it "routes, it does not think / hold authority." This lock pins that
it imports no authority / writer / retrieval / persistence / model / endpoint machinery,
at module level or lazily.

CHARACTERIZATION, not a safety proof. It imports no production module (the source is
parsed, never imported), so it has no runtime side effects. No endpoint/API/schema,
prompt mutation/exposure, output/review/control, writer/memory/persistence, Gate A /
Gate D, database/substrate, or audit-owner movement.

Non-duplication (deliberate):
  The forbidden direct-CALL absence for ``thinking_controller.py`` is ALREADY owned by
  C1 in ``tests/test_gate_a_tests_only_locks_c1_c5.py`` (its ``ADVISORY_MODULES`` +
  ``FORBIDDEN_CALL_NAMES``). C1 is explicitly call-name-only ("no import"). This file
  locks ONLY the complementary, currently-unguarded IMPORT SURFACE.

Allowed import surface:
  - stdlib: ``__future__``, ``os``, ``re``, ``typing``
  - sibling advisory / model surfaces: ``.thinking_models``, ``.stance_policy``,
    ``.reflection_trace``
Anything else (``fabric`` / ``app`` / ``agent_loop`` / retrieval / persistence / writer /
memory-graph / promotion / model-provider / endpoint / Gate A / Gate D / audit-owner)
trips the lock for review.
"""
from __future__ import annotations

import ast
import unittest
from pathlib import Path

# Project root (torment_fabric/) -> torment_service/.
_SERVICE_DIR = Path(__file__).resolve().parents[1] / "torment_service"
_MODULE = "thinking_controller.py"

# Bare ``import X`` names allowed (stdlib only).
_ALLOWED_BARE_IMPORTS = frozenset({"os", "re"})

# ``from M import ...`` modules allowed (stdlib + advisory siblings).
_ALLOWED_FROM_MODULES = frozenset({
    "__future__", "typing",
    "thinking_models", "stance_policy", "reflection_trace",
})

# Illustrative forbidden roots (the allowlist above is the real lock; this set only
# sharpens failure messages and the has-teeth self-test).
_FORBIDDEN_IMPORT_SUBSTRINGS = (
    "fabric", "app", "agent_loop", "retrieval", "assemble", "scoring",
    "persist", "store", "sqlite", "memory_graph", "deep_memory", "promotion",
    "spine", "writer", "provider", "llm_client", "endpoint", "schema",
    "gate_a", "gate_d", "audit_private", "audit_selected", "audit_evidence",
)


def _parse(filename: str) -> ast.AST:
    """Parse a torment_service source file. Source-only; never imported."""
    path = _SERVICE_DIR / filename
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _imported_module_strings(tree: ast.AST):
    """Every imported module path as a string: ``import a.b`` -> 'a.b';
    ``from .x import y`` -> 'x'; ``from a.b import y`` -> 'a.b'. Walks the whole
    tree, so lazy / in-function imports are included."""
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            out.extend(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            out.append(node.module or "")
    return out


class TestThinkingControllerImportSurface(unittest.TestCase):
    def test_only_allowed_imports(self):
        tree = _parse(_MODULE)
        offenders = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name not in _ALLOWED_BARE_IMPORTS:
                        offenders.append((node.lineno, f"import {alias.name}"))
            elif isinstance(node, ast.ImportFrom):
                if (node.module or "") not in _ALLOWED_FROM_MODULES:
                    offenders.append((node.lineno, f"from {node.module!r}"))
        self.assertEqual(
            offenders, [],
            "thinking_controller.py import surface must be bare "
            f"{sorted(_ALLOWED_BARE_IMPORTS)} + from {sorted(_ALLOWED_FROM_MODULES)}; "
            f"unexpected import(s): {offenders!r}",
        )

    def test_no_authority_writer_or_retrieval_imports(self):
        mods = _imported_module_strings(_parse(_MODULE))
        hits = [
            m for m in mods
            if any(s in m for s in _FORBIDDEN_IMPORT_SUBSTRINGS)
        ]
        self.assertEqual(
            hits, [],
            "thinking_controller.py must import no authority/writer/retrieval/persistence/"
            f"model/endpoint surface; found: {hits!r}",
        )

    def test_import_matcher_has_teeth(self):
        # A synthetic forbidden import IS flagged by both predicates.
        tree = ast.parse(
            "from .fabric import TormentFabric\n"
            "import torment_service.agent_loop as al\n"
        )
        from_offenders = [
            n.module for n in ast.walk(tree)
            if isinstance(n, ast.ImportFrom) and (n.module or "") not in _ALLOWED_FROM_MODULES
        ]
        bare_offenders = [
            a.name for n in ast.walk(tree) if isinstance(n, ast.Import)
            for a in n.names if a.name not in _ALLOWED_BARE_IMPORTS
        ]
        self.assertIn("fabric", from_offenders)
        self.assertTrue(any("agent_loop" in n for n in bare_offenders))


if __name__ == "__main__":
    unittest.main()
