"""tests/test_memory_to_prompt_real_retrieval_harness.py

Verifies the BOUNDED REAL-RETRIEVAL MANUAL HARNESS (tests/manual/...): the default is
fake / dry-run with NO real retrieval, NO provider, NO network, NO secrets; real retrieval
is reachable only behind the manual env gate and fails closed on missing env / data; the
real fabric is read-only via ``TormentFabric.query(...)`` (never instantiated in fake mode);
and the harness references no endpoint / app / provider / owner / bridge / persistence /
control route. Automated tests never set the gate, so they never touch real data or a server.
"""
from __future__ import annotations

import ast
import importlib.util
import os
import unittest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_HARNESS_PATH = os.path.join(_REPO_ROOT, "tests", "manual",
                             "memory_to_prompt_real_retrieval_harness.py")
_GATE = "TORMENT_MEMORY_TO_PROMPT_REAL_RETRIEVAL_DEMO"
_ENV_KEYS = [
    _GATE,
    "TORMENT_MEMORY_TO_PROMPT_REAL_RETRIEVAL_WORKSPACE_ID",
    "TORMENT_MEMORY_TO_PROMPT_REAL_RETRIEVAL_AGENT_ID",
    "TORMENT_MEMORY_TO_PROMPT_REAL_RETRIEVAL_QUERY",
    "TORMENT_MEMORY_TO_PROMPT_REAL_RETRIEVAL_TOP_K",
    "TORMENT_MEMORY_TO_PROMPT_REAL_RETRIEVAL_DOMAIN_ID",
    "TORMENT_MEMORY_TO_PROMPT_REAL_RETRIEVAL_DATA_DIR",
]


def _load_harness():
    spec = importlib.util.spec_from_file_location(
        "memory_to_prompt_real_retrieval_harness", _HARNESS_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class _EnvCleared(unittest.TestCase):
    """Clear the real-retrieval gate and all related env for every automated test."""

    def setUp(self):
        self._saved = {k: os.environ.pop(k, None) for k in _ENV_KEYS}

    def tearDown(self):
        for k, v in self._saved.items():
            if v is not None:
                os.environ[k] = v


class TestDefaultIsFakeNoRealRetrieval(_EnvCleared):
    def setUp(self):
        super().setUp()
        self.h = _load_harness()

    def test_gate_helper_truth_table(self):
        self.assertFalse(self.h.real_retrieval_gate_enabled({}))
        self.assertFalse(self.h.real_retrieval_gate_enabled({_GATE: ""}))
        self.assertFalse(self.h.real_retrieval_gate_enabled({_GATE: "0"}))
        self.assertTrue(self.h.real_retrieval_gate_enabled({_GATE: "1"}))

    def test_default_mode_is_fake(self):
        obs = self.h.run_demo()  # gate unset -> fake/dry-run
        self.assertFalse(obs["real_retrieval_enabled"])
        self.assertFalse(obs["retrieval_called"])
        self.assertFalse(obs["provider_called"])
        self.assertTrue(obs["model_called"])

    def test_default_proves_safe_memory_to_prompt_shape(self):
        obs = self.h.run_demo(use_real=False)
        self.assertTrue(obs["model_called"])
        self.assertIsNotNone(obs["memory_index"])
        self.assertIsNotNone(obs["raw_index"])
        self.assertTrue(obs["memory_before_raw"])
        self.assertTrue(obs["raw_is_separate"])
        self.assertTrue(obs["memory_has_label"])
        self.assertTrue(obs["memory_not_persisted"])
        self.assertTrue(obs["result_has_no_memory_field"])
        self.assertFalse(obs["source_data_mutated"])

    def test_no_real_fabric_instantiated_in_fake_mode(self):
        # CI-safe: with the gate unset / fake mode, the REAL TormentFabric is never
        # instantiated. Spy on the harness's TormentFabric reference.
        instantiated = []

        class _SpyFabric:
            def __init__(self, *a, **k):
                instantiated.append((a, k))

        orig = self.h.TormentFabric
        self.h.TormentFabric = _SpyFabric
        try:
            obs = self.h.run_demo(use_real=False)
        finally:
            self.h.TormentFabric = orig
        self.assertEqual(instantiated, [], "real fabric must not be instantiated in fake mode")
        self.assertFalse(obs["retrieval_called"])

    def test_gated_missing_env_fails_closed_without_touching_data(self):
        # Gate on, but the required workspace/agent/query env are absent -> RuntimeError
        # BEFORE any fabric instantiation or data access.
        instantiated = []

        class _SpyFabric:
            def __init__(self, *a, **k):
                instantiated.append((a, k))

        orig = self.h.TormentFabric
        self.h.TormentFabric = _SpyFabric
        try:
            with self.assertRaises(RuntimeError):
                self.h.run_demo(use_real=True, env={_GATE: "1"})
        finally:
            self.h.TormentFabric = orig
        self.assertEqual(instantiated, [],
                         "no real fabric may be instantiated when required env is missing")


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

    def _import_roots(self):
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
        self.assertIn("TormentFabric", names)
        self.assertIn("query", names)
        self.assertIn(_GATE, self.src)

    def test_no_owner_bridge_audit_or_mutation_idents(self):
        names = self._names()
        for forbidden in ("PrivateGenerationOwner", "audit_private_generation_owner",
                          "audit_selected_items_runner_bridge",
                          "run_turn_with_selected_items_observation",
                          "selected_admitted_items", "audit_admitted_context_items",
                          "retrieve_assembled", "ArchiveStore",
                          "reinforce", "promote", "promote_chunk", "writeback",
                          "increment_retrieval_counts"):
            self.assertNotIn(forbidden, names, f"harness must not reference {forbidden}")

    def test_no_endpoint_client_or_provider_substrings(self):
        for substr in ("/agent/query", "/retrieve", "TestClient", "requests", "httpx",
                       "app.py", "retrieve_assembled", "ArchiveStore",
                       "anthropic", "openai", "OpenAI", "OpenRouter"):
            self.assertNotIn(substr, self.src, f"harness must not contain {substr!r}")

    def test_no_app_provider_network_imports(self):
        roots = self._import_roots()
        for forbidden in ("app", "requests", "httpx", "aiohttp", "urllib", "socket",
                          "anthropic", "openai"):
            self.assertNotIn(forbidden, roots, f"harness must not import {forbidden}")

    def test_no_persistence_or_log_writers(self):
        for substr in ("save_transcript", "write_log", "jsonl",
                       "logging.FileHandler", "write_text"):
            self.assertNotIn(substr, self.src, f"harness must not contain {substr!r}")
        writes = [n for n in ast.walk(self.tree)
                  if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                  and n.func.id == "open"]
        self.assertEqual(writes, [], "harness must open no files")

    def test_no_control_steering_idents(self):
        names = self._names()
        for forbidden in ("retry", "rerank", "suppress", "review_control", "style_steer"):
            self.assertNotIn(forbidden, names, f"harness must not implement {forbidden}")


class TestHarnessNotReachableFromProduction(unittest.TestCase):
    def test_no_production_module_references_harness(self):
        service = os.path.join(_REPO_ROOT, "torment_service")
        refs = []
        for dp, dns, fns in os.walk(service):
            dns[:] = [d for d in dns if d != "__pycache__" and not d.startswith("do_not_touch")]
            for fn in fns:
                if not fn.endswith(".py"):
                    continue
                with open(os.path.join(dp, fn), "rb") as fh:
                    if b"memory_to_prompt_real_retrieval_harness" in fh.read():
                        refs.append(fn)
        self.assertEqual(refs, [],
                         f"harness must be referenced by no production module; got {refs}")


if __name__ == "__main__":
    unittest.main()
