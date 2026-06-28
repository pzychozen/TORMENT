"""tests/test_memory_to_prompt_provider_llm_harness.py

Verifies the BOUNDED PROVIDER / MANUAL HARNESS (tests/manual/...): the default is
fake / dry-run with NO provider call and NO module-level provider import; the provider path
is reachable only behind the manual env gate; and the harness references no endpoint / app /
owner / bridge / audit / persistence / control route. Automated tests never set the gate, so
they never touch a provider or need secrets / network.
"""
from __future__ import annotations

import ast
import importlib.util
import os
import unittest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_HARNESS_PATH = os.path.join(_REPO_ROOT, "tests", "manual",
                             "memory_to_prompt_provider_llm_harness.py")
_GATE = "TORMENT_MEMORY_TO_PROMPT_PROVIDER_DEMO"


def _load_harness():
    spec = importlib.util.spec_from_file_location(
        "memory_to_prompt_provider_llm_harness", _HARNESS_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class _GateCleared(unittest.TestCase):
    """Ensure the manual provider gate is UNSET for every automated test."""

    def setUp(self):
        self._saved_gate = os.environ.pop(_GATE, None)

    def tearDown(self):
        if self._saved_gate is not None:
            os.environ[_GATE] = self._saved_gate


class TestDefaultIsFakeNoProvider(_GateCleared):
    def setUp(self):
        super().setUp()
        self.h = _load_harness()

    def test_provider_gate_helper_truth_table(self):
        self.assertFalse(self.h.provider_gate_enabled({}))
        self.assertFalse(self.h.provider_gate_enabled({_GATE: "0"}))
        self.assertFalse(self.h.provider_gate_enabled({_GATE: ""}))
        self.assertTrue(self.h.provider_gate_enabled({_GATE: "1"}))

    def test_default_mode_is_fake_no_provider_call(self):
        obs = self.h.run_demo()  # gate unset -> fake/dry-run
        self.assertFalse(obs["provider_enabled"])
        self.assertFalse(obs["provider_called"])
        self.assertTrue(obs["model_called"])

    def test_build_fake_runner_does_not_import_provider_or_raise(self):
        # The fake path must build without a provider package or key, and never imports the
        # provider package (proven statically in the source-boundary tests).
        runner, fabric, llm, provider_enabled = self.h.build_demo_runner(use_provider=False)
        self.assertFalse(provider_enabled)
        self.assertFalse(getattr(llm, "provider_called", False))

    def test_explicit_fake_proves_safe_memory_to_prompt_shape(self):
        obs = self.h.run_demo(use_provider=False)
        self.assertTrue(obs["model_called"])
        self.assertFalse(obs["provider_enabled"])
        self.assertFalse(obs["provider_called"])
        self.assertIsNotNone(obs["memory_index"])
        self.assertIsNotNone(obs["raw_index"])
        self.assertTrue(obs["memory_before_raw"])
        self.assertTrue(obs["raw_is_separate"])
        self.assertTrue(obs["memory_has_label"])
        self.assertTrue(obs["memory_not_persisted"])
        self.assertTrue(obs["result_has_no_memory_field"])


class TestHarnessSourceBoundaries(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(_HARNESS_PATH, "r", encoding="utf-8") as fh:
            cls.src = fh.read()
        cls.tree = ast.parse(cls.src)

    def _names(self):
        names = set()
        for n in ast.walk(self.tree):
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

    def _top_level_import_roots(self):
        roots = set()
        for n in self.tree.body:  # module-level statements only
            if isinstance(n, ast.Import):
                roots.update(a.name.split(".")[0] for a in n.names)
            elif isinstance(n, ast.ImportFrom) and n.module:
                roots.add(n.module.split(".")[0])
        return roots

    def _all_import_roots(self):
        roots = set()
        for n in ast.walk(self.tree):
            if isinstance(n, ast.Import):
                roots.update(a.name.split(".")[0] for a in n.names)
            elif isinstance(n, ast.ImportFrom) and n.module:
                roots.add(n.module.split(".")[0])
        return roots

    def test_required_symbols_present(self):
        names = self._names()
        self.assertIn("run_turn_with_memory_context", names)
        self.assertIn("memory_context_orchestrator", names)
        self.assertIn(_GATE, self.src)

    def test_no_owner_bridge_or_audit_routes(self):
        names = self._names()
        for forbidden in ("PrivateGenerationOwner", "audit_private_generation_owner",
                          "audit_selected_items_runner_bridge",
                          "run_turn_with_selected_items_observation",
                          "selected_admitted_items", "audit_admitted_context_items"):
            self.assertNotIn(forbidden, names, f"harness must not reference {forbidden}")

    def test_no_endpoint_route_or_http_client_substrings(self):
        for substr in ("/agent/query", "/retrieve", "TestClient",
                       "requests.post", "requests.get"):
            self.assertNotIn(substr, self.src, f"harness must not contain {substr!r}")

    def test_no_app_or_network_db_imports_provider_allowed(self):
        roots = self._all_import_roots()
        for forbidden in ("app", "requests", "httpx", "aiohttp", "urllib", "socket",
                          "sqlite3", "psycopg2", "boto3", "openai"):
            self.assertNotIn(forbidden, roots, f"harness must not import {forbidden}")

    def test_provider_package_imported_only_lazily(self):
        self.assertNotIn("anthropic", self._top_level_import_roots(),
                         "provider package must be imported lazily inside a function")
        self.assertIn("anthropic", self._all_import_roots(),
                      "provider package import (lazy, inside the adapter) should be present")

    def test_no_persistence_or_log_writers(self):
        for substr in ("write_text", "jsonl", "save_transcript", "write_log",
                       "logging.FileHandler", "sqlite3", "psycopg2", "boto3"):
            self.assertNotIn(substr, self.src, f"harness must not contain {substr!r}")
        opens = [n for n in ast.walk(self.tree)
                 if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                 and n.func.id == "open"]
        self.assertEqual(opens, [], "harness must open no files")

    def test_no_control_steering_idents(self):
        names = self._names()
        for forbidden in ("retry", "rerank", "suppress", "review_control", "style_steer"):
            self.assertNotIn(forbidden, names, f"harness must not implement {forbidden}")


class TestProviderNotReachableFromProduction(unittest.TestCase):
    def test_no_production_module_references_provider_harness(self):
        service = os.path.join(_REPO_ROOT, "torment_service")
        refs = []
        for dp, dns, fns in os.walk(service):
            dns[:] = [d for d in dns if d != "__pycache__" and not d.startswith("do_not_touch")]
            for fn in fns:
                if not fn.endswith(".py"):
                    continue
                with open(os.path.join(dp, fn), "rb") as fh:
                    if b"memory_to_prompt_provider_llm_harness" in fh.read():
                        refs.append(fn)
        self.assertEqual(refs, [],
                         f"provider harness must be referenced by no production module; got {refs}")


if __name__ == "__main__":
    unittest.main()
