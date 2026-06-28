"""tests/test_memory_to_prompt_memory_context_orchestrator.py

Tests for the DORMANT / test-called memory-to-prompt orchestrator (candidate 6):
``torment_service/memory_context_orchestrator.py``.

It owns assembly (calls ``assemble_context`` as a function), derives bounded read-only
memory text from ``AssembledContext.assembled_text``, and invokes authoritative
``runner.run_turn(..., memory_context_text=...)``. It passes NO audit items, imports no
app/owner/bridge/U1/storage route, and is called nowhere in production.
"""
from __future__ import annotations

import ast
import os
import types
import unittest

from torment_service import memory_context_orchestrator as orch
from torment_service.retrieval_assembler import AssembledContext


def _assembled(text, **extra):
    return AssembledContext(profile="companion", token_budget=4000, assembled_text=text, **extra)


class _SpyRunner:
    def __init__(self):
        self.calls = []

    def run_turn(self, **kwargs):
        self.calls.append(kwargs)
        return types.SimpleNamespace(turn="ok", kwargs=kwargs)


class TestDeriveBoundedText(unittest.TestCase):
    def test_derives_stripped_text_from_assembled_text(self):
        out = orch._memory_context_text_from_assembled_context(_assembled("  recalled fact  "))
        self.assertEqual(out, "recalled fact")

    def test_empty_or_whitespace_assembled_text_yields_none(self):
        for t in ("", "   ", "\n\t "):
            self.assertIsNone(
                orch._memory_context_text_from_assembled_context(_assembled(t)),
                f"assembled_text {t!r} should yield None (memory-blind)")

    def test_source_is_only_assembled_text(self):
        # Deriving uses ONLY .assembled_text — populated blocks with empty assembled_text
        # still yield None (no raw/other content is used as memory).
        ac = _assembled("", blocks={"identity": [{"text": "should not be used"}]})
        self.assertIsNone(orch._memory_context_text_from_assembled_context(ac))


class TestOrchestratorRunTurn(unittest.TestCase):
    def _patch_assemble(self, fn):
        orig = orch.assemble_context
        orch.assemble_context = fn
        self.addCleanup(lambda: setattr(orch, "assemble_context", orig))

    def test_calls_assemble_and_passes_bounded_text_to_run_turn(self):
        runner = _SpyRunner()
        captured = {}

        def fake_assemble(**kwargs):
            captured.update(kwargs)
            return _assembled("a recalled fact")

        self._patch_assemble(fake_assemble)
        orch.run_turn_with_memory_context(
            runner, workspace_id="ws", agent_id="agent",
            observation=types.SimpleNamespace(text="hi"), step=1,
            core_hits=[{"text": "x"}])
        # assemble_context was consumed as a function with the retrieval inputs
        self.assertEqual(captured["core_hits"], [{"text": "x"}])
        # run_turn received the bounded memory text and the normal runner args
        self.assertEqual(len(runner.calls), 1)
        call = runner.calls[0]
        self.assertEqual(call["memory_context_text"], "a recalled fact")
        self.assertEqual(call["workspace_id"], "ws")
        self.assertEqual(call["agent_id"], "agent")
        self.assertEqual(call["step"], 1)

    def test_empty_assembled_text_passes_none(self):
        runner = _SpyRunner()
        self._patch_assemble(lambda **k: _assembled("   "))
        orch.run_turn_with_memory_context(
            runner, workspace_id="ws", agent_id="agent",
            observation=types.SimpleNamespace(text="hi"), step=1, core_hits=[])
        self.assertIsNone(runner.calls[0]["memory_context_text"])

    def test_no_audit_items_routed_into_run_turn(self):
        runner = _SpyRunner()
        self._patch_assemble(lambda **k: _assembled("fact"))
        orch.run_turn_with_memory_context(
            runner, workspace_id="ws", agent_id="agent",
            observation=types.SimpleNamespace(text="hi"), step=1, core_hits=[])
        self.assertNotIn("audit_admitted_context_items", runner.calls[0],
                         "orchestrator must not route audit items into run_turn")


class TestOrchestratorBoundaries(unittest.TestCase):
    @staticmethod
    def _service_dir():
        return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "torment_service")

    def _module_tree(self):
        with open(os.path.join(self._service_dir(), "memory_context_orchestrator.py"), "rb") as fh:
            return ast.parse(fh.read().replace(b"\x00", b""))

    def _import_names(self, tree):
        names = set()
        for n in ast.walk(tree):
            if isinstance(n, ast.ImportFrom) and n.module:
                names.add(n.module.split(".")[-1])
                for a in n.names:
                    names.add(a.name)
            elif isinstance(n, ast.Import):
                for a in n.names:
                    names.add(a.name.split(".")[-1])
        return names

    def test_imports_retrieval_assembler_only_no_forbidden_routes(self):
        names = self._import_names(self._module_tree())
        self.assertIn("retrieval_assembler", names)
        self.assertIn("assemble_context", names)
        for forbidden in ("app", "PrivateGenerationOwner", "audit_private_generation_owner",
                          "audit_selected_items_runner_bridge",
                          "run_turn_with_selected_items_observation", "selected_admitted_items"):
            self.assertNotIn(forbidden, names,
                             f"orchestrator must not import/reference {forbidden}")

    def test_no_write_persistence_or_control_idents(self):
        tree = self._module_tree()
        idents = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
        idents |= {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
        for forbidden in ("ingest", "persist", "save", "write_memory",
                          "audit_admitted_context_items", "observe_prompt_inclusion_packet"):
            self.assertNotIn(forbidden, idents,
                             f"orchestrator must not reference {forbidden}")

    def test_called_nowhere_in_production(self):
        # No torment_service module imports/references the orchestrator (dormant).
        importers = []
        for dp, dns, fns in os.walk(self._service_dir()):
            dns[:] = [d for d in dns if d != "__pycache__" and not d.startswith("do_not_touch")]
            for fn in fns:
                if not fn.endswith(".py") or fn == "memory_context_orchestrator.py":
                    continue
                with open(os.path.join(dp, fn), "rb") as fh:
                    src = fh.read()
                if b"memory_context_orchestrator" in src or b"run_turn_with_memory_context" in src:
                    importers.append(fn)
        self.assertEqual(importers, [],
                         f"orchestrator must be called nowhere in production; importers: {importers}")


if __name__ == "__main__":
    unittest.main()
