"""tests/test_memory_to_prompt_operator_demo_harness.py

Verifies the CONTROLLED OPERATOR DEMO HARNESS (tests/manual/...): it demonstrates the
dormant memory-to-prompt orchestrator with fake / capturing boundaries only — the memory
block is labelled read-only guidance and ordered BEFORE the raw input, with no provider /
persistence / endpoint / audit-owner path — and it is imported by no production module.
"""
from __future__ import annotations

import ast
import importlib.util
import os
import unittest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_HARNESS_PATH = os.path.join(_REPO_ROOT, "tests", "manual",
                             "memory_to_prompt_operator_demo_harness.py")


def _load_harness():
    spec = importlib.util.spec_from_file_location(
        "memory_to_prompt_operator_demo_harness", _HARNESS_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestHarnessDemonstratesSafeMemoryToPrompt(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.h = _load_harness()
        cls.obs = cls.h.run_demo()

    def test_harness_imports_and_runs_without_provider_or_state(self):
        # run_demo completed (in setUpClass) using fake boundaries; the model boundary was
        # exercised via the fake capturing LLM (no provider, no secrets, no runtime state).
        self.assertTrue(self.obs["model_called"],
                        "demo should exercise the captured prompt path via the fake LLM")

    def test_memory_block_appears_before_raw_input(self):
        self.assertIsNotNone(self.obs["memory_index"], "memory block not found in prompt")
        self.assertIsNotNone(self.obs["raw_index"], "raw user input not found in prompt")
        self.assertTrue(self.obs["memory_before_raw"],
                        "memory block must appear before the raw user input")

    def test_raw_input_is_separate_and_later(self):
        self.assertTrue(self.obs["raw_is_separate"],
                        "raw user input must remain its own separate message")

    def test_memory_block_is_read_only_guidance_label(self):
        self.assertTrue(self.obs["memory_has_label"],
                        "memory block must carry the read-only guidance label")

    def test_no_memory_persistence(self):
        self.assertTrue(self.obs["memory_not_persisted"],
                        "memory context must not be persisted via ingest")

    def test_memory_not_exposed_on_turn_result(self):
        self.assertTrue(self.obs["result_has_no_memory_field"],
                        "memory context must not be exposed on TurnResult")


class TestHarnessSourceBoundaries(unittest.TestCase):
    def _tree(self):
        with open(_HARNESS_PATH, "rb") as fh:
            return ast.parse(fh.read().replace(b"\x00", b""))

    def _names(self, tree):
        names = set()
        for n in ast.walk(tree):
            if isinstance(n, ast.ImportFrom) and n.module:
                names.add(n.module.split(".")[-1])
                for a in n.names:
                    names.add(a.name)
            elif isinstance(n, ast.Import):
                for a in n.names:
                    names.add(a.name.split(".")[-1])
            elif isinstance(n, ast.Attribute):
                names.add(n.attr)
            elif isinstance(n, ast.Name):
                names.add(n.id)
        return names

    def test_calls_orchestrator_entrypoint_directly(self):
        names = self._names(self._tree())
        self.assertIn("memory_context_orchestrator", names)
        self.assertIn("run_turn_with_memory_context", names,
                      "harness must call the orchestrator entrypoint directly")

    def test_no_endpoint_owner_bridge_or_audit_routes(self):
        names = self._names(self._tree())
        for forbidden in ("app", "PrivateGenerationOwner", "audit_private_generation_owner",
                          "audit_selected_items_runner_bridge",
                          "run_turn_with_selected_items_observation", "selected_admitted_items",
                          "audit_admitted_context_items"):
            self.assertNotIn(forbidden, names,
                             f"harness must not reference {forbidden}")

    def test_no_provider_network_db_or_control_idents(self):
        names = self._names(self._tree())
        for forbidden in ("requests", "httpx", "urllib", "aiohttp", "openai", "anthropic",
                          "socket", "psycopg2", "sqlite3", "boto3"):
            self.assertNotIn(forbidden, names,
                             f"harness must not use provider/network/db module {forbidden}")
        for forbidden in ("retry", "rerank", "suppress", "review_control", "style_steer",
                          "persist", "save_transcript", "write_log"):
            self.assertNotIn(forbidden, names,
                             f"harness must not implement {forbidden}")

    def test_harness_imported_by_no_production_module(self):
        service = os.path.join(_REPO_ROOT, "torment_service")
        importers = []
        for dp, dns, fns in os.walk(service):
            dns[:] = [d for d in dns if d != "__pycache__" and not d.startswith("do_not_touch")]
            for fn in fns:
                if not fn.endswith(".py"):
                    continue
                with open(os.path.join(dp, fn), "rb") as fh:
                    if b"memory_to_prompt_operator_demo_harness" in fh.read():
                        importers.append(fn)
        self.assertEqual(importers, [],
                         f"harness must be referenced by no production module; got {importers}")


if __name__ == "__main__":
    unittest.main()
