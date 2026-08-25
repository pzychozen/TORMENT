"""tests/test_non_spine_llm_runtime_skeleton.py

Guards for the non-Spine LLM runtime skeleton, the provider-adapter contracts, the
callable-only MANUAL provider adapter, the production-internal MANUAL helper, and the
source-level fences around the first REAL provider adapter. The default / fake / callable
paths stay fake / dormant / test-called only.
"""
import ast
import dataclasses
import unittest
from pathlib import Path

import torment_service.non_spine_llm_runtime as nslr
from torment_service.non_spine_llm_runtime import (
    NonSpineLLMRuntime,
    NonSpineLLMRuntimeRequest,
    NonSpineLLMRuntimeResult,
    NonSpineLLMPromptRequest,
    NonSpineLLMCompletionAdapter,
    FakeNonSpineLLMCompletionAdapter,
    NonSpineLLMMemoryContext,
    NonSpineLLMProviderConfig,
    NonSpineLLMProviderRequest,
    NonSpineLLMProviderResult,
    NonSpineLLMProviderAdapter,
    FakeNonSpineLLMProviderAdapter,
    CallableNonSpineLLMProviderAdapter,
    run_non_spine_callable_provider_manual,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "torment_service" / "non_spine_llm_runtime.py"
MODULE_SRC = MODULE_PATH.read_text(encoding="utf-8")

MEMORY_LABEL = "MEMORY-CONTEXT (read-only guidance):"

FORBIDDEN_SUBSTRINGS = [
    "FastAPI", "@mcp.tool", "run_cognition_pipeline", "AgentRunner", "run_turn",
    "memory_context_orchestrator", "assemble_context", "AssembledContext",
    "retrieval_assembler", "TormentFabric", "openai", ".chat(", "ingest",
    "reinforce", "promote", "write", "transcript", "scheduler", "create_task",
    "Thread", "subprocess", "socket", "os.getenv", "getenv(", "dotenv",
]

TOPLEVEL_ALLOWED_IMPORTS = {"__future__", "copy", "dataclasses", "typing"}
NESTED_ALLOWED_IMPORTS = {"os", "anthropic"}
FORBIDDEN_IMPORTS_ANYWHERE = {
    "requests", "httpx", "aiohttp", "urllib", "socket", "ssl", "subprocess",
    "asyncio", "threading", "sqlite3", "pickle", "secrets", "dotenv", "logging",
    "openai",
}


def _import_roots(nodes):
    roots = set()
    for node in nodes:
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                roots.add(node.module.split(".")[0])
    return roots


def _toplevel_import_roots():
    return _import_roots(ast.parse(MODULE_SRC).body)


def _all_import_roots():
    return _import_roots(list(ast.walk(ast.parse(MODULE_SRC))))


class TestModuleShape(unittest.TestCase):
    def test_runtime_class_exists(self):
        self.assertTrue(hasattr(nslr, "NonSpineLLMRuntime"))
        self.assertIsInstance(NonSpineLLMRuntime, type)

    def test_request_and_result_exist(self):
        self.assertIsInstance(NonSpineLLMRuntimeRequest, type)
        self.assertIsInstance(NonSpineLLMRuntimeResult, type)


class TestMemoryContextPackage(unittest.TestCase):
    def test_frozen_dataclass_and_primitive(self):
        self.assertTrue(dataclasses.is_dataclass(NonSpineLLMMemoryContext))
        self.assertTrue(NonSpineLLMMemoryContext.__dataclass_params__.frozen)
        mc = NonSpineLLMMemoryContext.from_text("hello")
        self.assertIsInstance(mc.text, str)
        self.assertIsInstance(mc.max_chars, int)
        self.assertIsInstance(mc.was_truncated, bool)

    def test_from_text_strips_and_empty(self):
        self.assertEqual(NonSpineLLMMemoryContext.from_text("  padded  ").text, "padded")
        for raw in ("", "  ", "\n\t "):
            self.assertTrue(NonSpineLLMMemoryContext.from_text(raw).is_empty())

    def test_cap_and_flag(self):
        mc = NonSpineLLMMemoryContext.from_text("x" * 5000)
        self.assertEqual(len(mc.text), 1200)
        self.assertTrue(mc.was_truncated)
        self.assertFalse(NonSpineLLMMemoryContext.from_text("short").was_truncated)

    def test_is_governed_marker_only(self):
        mc = NonSpineLLMMemoryContext.from_text("m", is_governed=True)
        self.assertIs(mc.is_governed, True)
        self.assertIs(mc.is_read_only, True)


class TestMemoryContextWiring(unittest.TestCase):
    def test_build_and_render(self):
        pr = NonSpineLLMRuntime._build_prompt_request(
            NonSpineLLMRuntimeRequest(user_input="hi", memory_context_text="remembered alpha"))
        self.assertEqual(pr.memory_context.text, "remembered alpha")
        self.assertIn(MEMORY_LABEL, pr.rendered_prompt)
        self.assertIn("remembered alpha", pr.rendered_prompt)

    def test_empty_memory_renders_no_block(self):
        pr = NonSpineLLMRuntime._build_prompt_request(
            NonSpineLLMRuntimeRequest(user_input="hi", memory_context_text="   "))
        self.assertNotIn("MEMORY-CONTEXT", pr.rendered_prompt)
        self.assertIn("USER: hi", pr.rendered_prompt)


class TestProviderContracts(unittest.TestCase):
    def test_types_and_frozen(self):
        for cls in (NonSpineLLMProviderConfig, NonSpineLLMProviderRequest, NonSpineLLMProviderResult):
            self.assertTrue(dataclasses.is_dataclass(cls))
            self.assertTrue(cls.__dataclass_params__.frozen)

    def test_config_defaults_fake(self):
        cfg = NonSpineLLMProviderConfig()
        self.assertIs(cfg.is_fake, True)
        self.assertIs(cfg.network_enabled, False)
        self.assertEqual(cfg.provider_name, "fake")

    def test_base_adapter_raises(self):
        with self.assertRaises(NotImplementedError):
            NonSpineLLMProviderAdapter().generate(
                NonSpineLLMProviderRequest(prompt_request=NonSpineLLMPromptRequest()))

    def test_fake_provider_markers(self):
        res = FakeNonSpineLLMProviderAdapter().generate(
            NonSpineLLMProviderRequest(prompt_request=NonSpineLLMPromptRequest()))
        self.assertIs(res.is_fake, True)
        self.assertIs(res.provider_called, False)


class TestCallableProviderAdapter(unittest.TestCase):
    def _req(self, rendered="USER: hi"):
        return NonSpineLLMProviderRequest(prompt_request=NonSpineLLMPromptRequest(rendered_prompt=rendered))

    def test_subclass_and_markers(self):
        self.assertTrue(issubclass(CallableNonSpineLLMProviderAdapter, NonSpineLLMProviderAdapter))
        res = CallableNonSpineLLMProviderAdapter(lambda request: "manual text").generate(self._req("USER: hi"))
        self.assertEqual(res.text, "manual text")
        self.assertIs(res.provider_called, True)
        self.assertIs(res.is_fake, False)
        self.assertEqual(res.echoed_prompt, "USER: hi")

    def test_rejects_non_callable(self):
        with self.assertRaises(TypeError):
            CallableNonSpineLLMProviderAdapter("not callable")

    def test_callable_adapter_referenced_only_in_class_def_and_manual_helper(self):
        tree = ast.parse(MODULE_SRC)
        allowed = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "CallableNonSpineLLMProviderAdapter":
                allowed.append((node.lineno, node.end_lineno))
            if isinstance(node, ast.FunctionDef) and node.name == "run_non_spine_callable_provider_manual":
                allowed.append((node.lineno, node.end_lineno))
        for i, ln in enumerate(MODULE_SRC.splitlines(), start=1):
            if "CallableNonSpineLLMProviderAdapter" in ln:
                self.assertTrue(any(lo <= i <= hi for lo, hi in allowed),
                    "CallableNonSpineLLMProviderAdapter outside class def / helper at line %d" % i)

    def test_manual_helper_defined_not_called_in_module(self):
        tree = ast.parse(MODULE_SRC)
        called = [n for n in ast.walk(tree)
                  if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                  and n.func.id == "run_non_spine_callable_provider_manual"]
        self.assertEqual(called, [])


class TestProductionManualHelper(unittest.TestCase):
    def test_helper_result_and_markers(self):
        res = run_non_spine_callable_provider_manual(lambda request: "callable text", user_input="hi")
        self.assertIsInstance(res, NonSpineLLMRuntimeResult)
        self.assertEqual(res.response_text, "callable text")
        self.assertIs(res.provider_called, True)
        self.assertIs(res.is_fake, False)

    def test_default_runtime_path_remains_fake(self):
        result = NonSpineLLMRuntime().run(NonSpineLLMRuntimeRequest(user_input="hi"))
        self.assertIs(result.is_fake, True)
        self.assertIs(result.provider_called, False)
        self.assertIn("fake no-op", result.response_text)


class TestRunUsesFakeAdapter(unittest.TestCase):
    def _request(self):
        return NonSpineLLMRuntimeRequest(
            user_input="hello there", system_text="you are agent_x",
            memory_context_text="remembered detail alpha", extra_messages=("prior turn beta",))

    def test_fake_no_op_and_capture(self):
        result = NonSpineLLMRuntime().run(self._request())
        self.assertIs(result.is_fake, True)
        self.assertIs(result.provider_called, False)
        self.assertIn("fake no-op", result.response_text)
        self.assertIn(MEMORY_LABEL, result.rendered_prompt)
        self.assertIn("hello there", result.rendered_prompt)
        self.assertIn("remembered detail alpha", result.rendered_prompt)

    def test_default_completion_path_uses_fake_provider(self):
        pr = NonSpineLLMRuntime._build_prompt_request(NonSpineLLMRuntimeRequest(user_input="hi"))
        comp = FakeNonSpineLLMCompletionAdapter().complete(pr)
        self.assertIs(comp.is_fake, True)
        self.assertIs(comp.provider_called, False)

    def test_base_completion_adapter_raises(self):
        pr = NonSpineLLMRuntime._build_prompt_request(NonSpineLLMRuntimeRequest(user_input="hi"))
        with self.assertRaises(NotImplementedError):
            NonSpineLLMCompletionAdapter().complete(pr)

    def test_deterministic(self):
        req = self._request()
        self.assertEqual(NonSpineLLMRuntime().run(req), NonSpineLLMRuntime().run(req))


class TestModuleImports(unittest.TestCase):
    def test_toplevel_imports_stdlib_only(self):
        offending = _toplevel_import_roots() - TOPLEVEL_ALLOWED_IMPORTS
        self.assertEqual(offending, set(), "non-stdlib top-level imports: %s" % offending)

    def test_anthropic_not_imported_at_module_level(self):
        self.assertNotIn("anthropic", _toplevel_import_roots())

    def test_all_imports_within_allowed(self):
        offending = _all_import_roots() - (TOPLEVEL_ALLOWED_IMPORTS | NESTED_ALLOWED_IMPORTS)
        self.assertEqual(offending, set(), "unexpected imports: %s" % offending)

    def test_no_forbidden_imports_anywhere(self):
        offending = _all_import_roots() & FORBIDDEN_IMPORTS_ANYWHERE
        self.assertEqual(offending, set(), "forbidden imports: %s" % offending)

    def test_no_env_read_at_import_time(self):
        tree = ast.parse(MODULE_SRC)
        func_ranges = [(n.lineno, n.end_lineno) for n in ast.walk(tree)
                       if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]

        def in_func(lineno):
            return any(lo <= lineno <= hi for lo, hi in func_ranges)

        for node in ast.walk(tree):
            if (isinstance(node, ast.Attribute) and node.attr == "environ"
                    and isinstance(node.value, ast.Name) and node.value.id == "os"):
                self.assertTrue(in_func(node.lineno), "os.environ at import time (line %d)" % node.lineno)
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "getenv" and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "os"):
                self.assertTrue(in_func(node.lineno), "os.getenv at import time (line %d)" % node.lineno)

    def test_anthropic_adapter_never_instantiated_in_module(self):
        calls = [n for n in ast.walk(ast.parse(MODULE_SRC))
                 if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                 and n.func.id == "AnthropicNonSpineLLMProviderAdapter"]
        self.assertEqual(calls, [], "AnthropicNonSpineLLMProviderAdapter instantiated in module")


class TestForbiddenReferencesAbsent(unittest.TestCase):
    def test_forbidden_substrings_absent(self):
        present = [s for s in FORBIDDEN_SUBSTRINGS if s in MODULE_SRC]
        self.assertEqual(present, [], "forbidden substrings present: %s" % present)

    def test_complete_call_only_on_local_fake_adapter(self):
        self.assertNotIn(".chat(", MODULE_SRC)
        for ln in [ln for ln in MODULE_SRC.splitlines() if ".complete(" in ln]:
            self.assertIn("adapter.complete(", ln, "non-local .complete( call: %s" % ln.strip())

    def test_generate_call_only_on_local_provider_adapter(self):
        for ln in [ln for ln in MODULE_SRC.splitlines() if ".generate(" in ln]:
            self.assertIn("provider_adapter.generate(", ln, "non-local .generate( call: %s" % ln.strip())


class TestNoLiveWiring(unittest.TestCase):
    def _iter_target_sources(self):
        targets = [REPO_ROOT / "torment_service" / "app.py",
                   REPO_ROOT / "torment_service" / "spine.py",
                   REPO_ROOT / "torment_service" / "mcp_server.py"]
        for pkg in ("cognition", "roles"):
            targets.extend(sorted((REPO_ROOT / pkg).glob("*.py")))
        for path in targets:
            if path.exists():
                yield path, path.read_text(encoding="utf-8")

    def test_no_reference_to_new_module(self):
        offenders = [str(p.relative_to(REPO_ROOT)) for p, s in self._iter_target_sources()
                     if "non_spine_llm_runtime" in s]
        self.assertEqual(offenders, [], "live wiring found in: %s" % offenders)


class TestSpineLockPresent(unittest.TestCase):
    def test_spine_lock_file_present(self):
        lock = REPO_ROOT / "tests" / "test_spine_cognition_memory_context_characterization_lock.py"
        self.assertTrue(lock.exists())


if __name__ == "__main__":
    unittest.main()
