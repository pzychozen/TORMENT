"""tests/test_non_spine_llm_runtime_skeleton.py

Guards for the dormant, internal, non-Spine LLM runtime skeleton, the provider-adapter
readiness contracts, the callable-only MANUAL provider adapter, and the
production-internal MANUAL helper. Everything is fake / dormant / test-called only.
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
    NonSpineLLMCompletion,
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
    "retrieval_assembler", "TormentFabric", "openai", "anthropic", ".chat(",
    "ingest", "reinforce", "promote", "write", "transcript", "scheduler",
    "create_task", "Thread", "subprocess", "socket", "os.environ", "os.getenv",
    "getenv(", "dotenv",
]

ALLOWED_IMPORT_ROOTS = {"__future__", "dataclasses", "typing"}

FORBIDDEN_IMPORT_ROOTS = {
    "openai", "anthropic", "socket", "ssl", "http", "urllib", "subprocess",
    "requests", "httpx", "aiohttp", "asyncio", "threading", "sqlite3", "pickle",
    "os", "secrets", "dotenv",
}


def _module_import_roots():
    roots = set()
    for node in ast.walk(ast.parse(MODULE_SRC)):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:
                roots.add("<relative>")
            if node.module:
                roots.add(node.module.split(".")[0])
    return roots


class TestModuleShape(unittest.TestCase):
    def test_runtime_class_exists(self):
        self.assertTrue(hasattr(nslr, "NonSpineLLMRuntime"))
        self.assertIsInstance(NonSpineLLMRuntime, type)

    def test_request_and_result_exist(self):
        self.assertIsInstance(NonSpineLLMRuntimeRequest, type)
        self.assertIsInstance(NonSpineLLMRuntimeResult, type)

    def test_run_build_prompt_and_memory_context_callable(self):
        self.assertTrue(callable(getattr(NonSpineLLMRuntime, "run", None)))
        self.assertTrue(callable(getattr(NonSpineLLMRuntime, "_build_prompt_request", None)))
        self.assertTrue(callable(getattr(NonSpineLLMRuntime, "_build_memory_context", None)))


class TestMemoryContextPackage(unittest.TestCase):
    def test_memory_context_exists_and_is_frozen_dataclass(self):
        self.assertIsInstance(NonSpineLLMMemoryContext, type)
        self.assertTrue(dataclasses.is_dataclass(NonSpineLLMMemoryContext))
        params = getattr(NonSpineLLMMemoryContext, "__dataclass_params__", None)
        self.assertIsNotNone(params)
        self.assertTrue(params.frozen)

    def test_memory_context_fields_are_primitive(self):
        mc = NonSpineLLMMemoryContext.from_text("hello", source_label="src")
        self.assertIsInstance(mc.text, str)
        self.assertIsInstance(mc.source_label, str)
        self.assertIsInstance(mc.is_read_only, bool)
        self.assertIsInstance(mc.is_governed, bool)
        self.assertIsInstance(mc.max_chars, int)
        self.assertIsInstance(mc.was_truncated, bool)

    def test_from_text_strips_input(self):
        mc = NonSpineLLMMemoryContext.from_text("   padded text   ")
        self.assertEqual(mc.text, "padded text")

    def test_empty_or_whitespace_input_is_empty_package(self):
        for raw in ("", "    ", "\n\t  "):
            mc = NonSpineLLMMemoryContext.from_text(raw)
            self.assertEqual(mc.text, "")
            self.assertTrue(mc.is_empty())
            self.assertFalse(mc.was_truncated)

    def test_empty_classmethod_returns_empty_package(self):
        mc = NonSpineLLMMemoryContext.empty()
        self.assertEqual(mc.text, "")
        self.assertTrue(mc.is_empty())
        self.assertFalse(mc.was_truncated)

    def test_long_memory_is_capped_and_flagged(self):
        mc = NonSpineLLMMemoryContext.from_text("x" * 5000)
        self.assertEqual(len(mc.text), 1200)
        self.assertTrue(mc.was_truncated)
        self.assertEqual(mc.max_chars, 1200)

    def test_short_memory_not_truncated(self):
        mc = NonSpineLLMMemoryContext.from_text("short memory")
        self.assertEqual(mc.text, "short memory")
        self.assertFalse(mc.was_truncated)

    def test_is_governed_is_marker_only_no_authority(self):
        mc = NonSpineLLMMemoryContext.from_text("m", is_governed=True)
        self.assertIs(mc.is_governed, True)
        self.assertIs(mc.is_read_only, True)


class TestMemoryContextWiring(unittest.TestCase):
    def test_build_memory_context_returns_package(self):
        req = NonSpineLLMRuntimeRequest(memory_context_text="remembered alpha")
        mc = NonSpineLLMRuntime._build_memory_context(req)
        self.assertIsInstance(mc, NonSpineLLMMemoryContext)
        self.assertEqual(mc.text, "remembered alpha")

    def test_build_prompt_request_carries_package(self):
        req = NonSpineLLMRuntimeRequest(user_input="hi", memory_context_text="remembered alpha")
        pr = NonSpineLLMRuntime._build_prompt_request(req)
        self.assertIsInstance(pr, NonSpineLLMPromptRequest)
        self.assertIsInstance(pr.memory_context, NonSpineLLMMemoryContext)
        self.assertEqual(pr.memory_context.text, "remembered alpha")

    def test_rendered_prompt_includes_label_for_nonempty_memory(self):
        req = NonSpineLLMRuntimeRequest(user_input="hi", memory_context_text="remembered alpha")
        pr = NonSpineLLMRuntime._build_prompt_request(req)
        self.assertIn(MEMORY_LABEL, pr.rendered_prompt)
        self.assertIn("remembered alpha", pr.rendered_prompt)

    def test_empty_memory_renders_no_memory_block(self):
        req = NonSpineLLMRuntimeRequest(user_input="hi", memory_context_text="   ")
        pr = NonSpineLLMRuntime._build_prompt_request(req)
        self.assertNotIn("MEMORY-CONTEXT", pr.rendered_prompt)
        self.assertTrue(pr.memory_context.is_empty())
        self.assertIn("USER: hi", pr.rendered_prompt)


class TestProviderContracts(unittest.TestCase):
    def test_provider_contract_types_exist(self):
        for cls in (NonSpineLLMProviderConfig, NonSpineLLMProviderRequest,
                    NonSpineLLMProviderResult, NonSpineLLMProviderAdapter,
                    FakeNonSpineLLMProviderAdapter):
            self.assertIsInstance(cls, type)

    def test_config_request_result_are_frozen_dataclasses(self):
        for cls in (NonSpineLLMProviderConfig, NonSpineLLMProviderRequest,
                    NonSpineLLMProviderResult):
            self.assertTrue(dataclasses.is_dataclass(cls))
            self.assertTrue(cls.__dataclass_params__.frozen)

    def test_config_and_result_are_primitive_shaped(self):
        cfg = NonSpineLLMProviderConfig()
        for value in (cfg.provider_name, cfg.model_name):
            self.assertIsInstance(value, str)
        for value in (cfg.is_fake, cfg.network_enabled):
            self.assertIsInstance(value, bool)
        res = FakeNonSpineLLMProviderAdapter().generate(
            NonSpineLLMProviderRequest(prompt_request=NonSpineLLMPromptRequest()))
        for value in (res.text, res.provider_name, res.model_name, res.echoed_prompt):
            self.assertIsInstance(value, str)
        for value in (res.is_fake, res.provider_called):
            self.assertIsInstance(value, bool)

    def test_config_defaults_are_fake_and_network_disabled(self):
        cfg = NonSpineLLMProviderConfig()
        self.assertIs(cfg.is_fake, True)
        self.assertIs(cfg.network_enabled, False)
        self.assertEqual(cfg.provider_name, "fake")

    def test_provider_base_adapter_raises(self):
        req = NonSpineLLMProviderRequest(prompt_request=NonSpineLLMPromptRequest())
        with self.assertRaises(NotImplementedError):
            NonSpineLLMProviderAdapter().generate(req)

    def test_fake_provider_adapter_returns_result_deterministic(self):
        req = NonSpineLLMProviderRequest(
            prompt_request=NonSpineLLMPromptRequest(rendered_prompt="USER: hi"))
        adapter = FakeNonSpineLLMProviderAdapter()
        self.assertIsInstance(adapter.generate(req), NonSpineLLMProviderResult)
        self.assertEqual(adapter.generate(req), adapter.generate(req))

    def test_fake_provider_result_markers(self):
        req = NonSpineLLMProviderRequest(prompt_request=NonSpineLLMPromptRequest())
        res = FakeNonSpineLLMProviderAdapter().generate(req)
        self.assertIs(res.is_fake, True)
        self.assertIs(res.provider_called, False)


class TestCallableProviderAdapter(unittest.TestCase):
    def _req(self, rendered="USER: hi"):
        return NonSpineLLMProviderRequest(
            prompt_request=NonSpineLLMPromptRequest(rendered_prompt=rendered))

    def test_exists_and_subclasses_provider_adapter(self):
        self.assertIsInstance(CallableNonSpineLLMProviderAdapter, type)
        self.assertTrue(issubclass(CallableNonSpineLLMProviderAdapter, NonSpineLLMProviderAdapter))

    def test_requires_injected_callable(self):
        adapter = CallableNonSpineLLMProviderAdapter(lambda request: "ok")
        self.assertIsInstance(adapter, CallableNonSpineLLMProviderAdapter)

    def test_rejects_non_callable(self):
        with self.assertRaises(TypeError):
            CallableNonSpineLLMProviderAdapter("not callable")

    def test_generate_passes_provider_request_to_callable(self):
        seen = []
        def _cb(request):
            seen.append(request)
            return "manual text"
        CallableNonSpineLLMProviderAdapter(_cb).generate(self._req())
        self.assertEqual(len(seen), 1)
        self.assertIsInstance(seen[0], NonSpineLLMProviderRequest)

    def test_converts_string_output_to_result_with_markers(self):
        res = CallableNonSpineLLMProviderAdapter(lambda request: "manual text").generate(self._req("USER: hi"))
        self.assertIsInstance(res, NonSpineLLMProviderResult)
        self.assertEqual(res.text, "manual text")
        self.assertIs(res.provider_called, True)
        self.assertIs(res.is_fake, False)
        self.assertEqual(res.echoed_prompt, "USER: hi")

    def test_coerces_non_string_output_to_str(self):
        res = CallableNonSpineLLMProviderAdapter(lambda request: 123).generate(self._req())
        self.assertIsInstance(res.text, str)
        self.assertEqual(res.text, "123")

    def test_deterministic_when_callable_deterministic(self):
        adapter = CallableNonSpineLLMProviderAdapter(lambda request: "stable")
        self.assertEqual(adapter.generate(self._req()), adapter.generate(self._req()))

    def test_callable_adapter_referenced_only_in_class_def_and_manual_helper(self):
        tree = ast.parse(MODULE_SRC)
        allowed_ranges = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "CallableNonSpineLLMProviderAdapter":
                allowed_ranges.append((node.lineno, node.end_lineno))
            if isinstance(node, ast.FunctionDef) and node.name == "run_non_spine_callable_provider_manual":
                allowed_ranges.append((node.lineno, node.end_lineno))
        self.assertTrue(allowed_ranges, "expected class def + manual helper to exist")
        for i, ln in enumerate(MODULE_SRC.splitlines(), start=1):
            if "CallableNonSpineLLMProviderAdapter" in ln:
                in_allowed = any(lo <= i <= hi for (lo, hi) in allowed_ranges)
                self.assertTrue(in_allowed,
                    "CallableNonSpineLLMProviderAdapter referenced outside class def / manual helper at line %d: %s" % (i, ln.strip()))

    def test_manual_helper_defined_not_called_in_module(self):
        tree = ast.parse(MODULE_SRC)
        defined = any(
            isinstance(n, ast.FunctionDef)
            and n.name == "run_non_spine_callable_provider_manual"
            for n in ast.walk(tree)
        )
        self.assertTrue(defined, "manual helper must be defined")
        called = [
            n for n in ast.walk(tree)
            if isinstance(n, ast.Call)
            and isinstance(n.func, ast.Name)
            and n.func.id == "run_non_spine_callable_provider_manual"
        ]
        self.assertEqual(called, [], "manual helper called within module")


class TestProductionManualHelper(unittest.TestCase):
    def _run(self, completion_callable, **kw):
        return run_non_spine_callable_provider_manual(completion_callable, **kw)

    def test_helper_exists(self):
        self.assertTrue(callable(run_non_spine_callable_provider_manual))

    def test_helper_returns_runtime_result(self):
        self.assertIsInstance(self._run(lambda request: "out", user_input="hi"), NonSpineLLMRuntimeResult)

    def test_injected_callable_receives_provider_request(self):
        seen = []
        def _cb(request):
            seen.append(request)
            return "out"
        self._run(_cb, user_input="hi")
        self.assertEqual(len(seen), 1)
        self.assertIsInstance(seen[0], NonSpineLLMProviderRequest)

    def test_result_carries_callable_text_and_markers(self):
        res = self._run(lambda request: "callable text", user_input="hi")
        self.assertEqual(res.response_text, "callable text")
        self.assertEqual(res.completion.text, "callable text")
        self.assertIs(res.provider_called, True)
        self.assertIs(res.is_fake, False)

    def test_result_carries_prompt_capture(self):
        res = self._run(lambda request: "x", user_input="hello there", system_text="sys")
        self.assertIsInstance(res.prompt_request, NonSpineLLMPromptRequest)
        self.assertIn("USER: hello there", res.rendered_prompt)
        self.assertIn("SYSTEM: sys", res.rendered_prompt)

    def test_memory_context_renders_through_label(self):
        res = self._run(lambda request: "x", user_input="hi", memory_context_text="remember me")
        self.assertIn(MEMORY_LABEL, res.rendered_prompt)
        self.assertIn("remember me", res.rendered_prompt)

    def test_default_runtime_path_remains_fake(self):
        result = NonSpineLLMRuntime().run(NonSpineLLMRuntimeRequest(user_input="hi"))
        self.assertIs(result.is_fake, True)
        self.assertIs(result.provider_called, False)
        self.assertIn("fake no-op", result.response_text)


class TestCompletionDelegatesToProvider(unittest.TestCase):
    def test_completion_adapter_delegates_to_provider(self):
        calls = []
        class _SpyProvider(NonSpineLLMProviderAdapter):
            def generate(self, request):
                calls.append(request)
                return NonSpineLLMProviderResult(
                    text="spy text", is_fake=True, provider_called=False,
                    provider_name=request.config.provider_name,
                    model_name=request.config.model_name,
                    echoed_prompt=request.prompt_request.rendered_prompt)
        adapter = FakeNonSpineLLMCompletionAdapter(provider_adapter=_SpyProvider())
        pr = NonSpineLLMRuntime._build_prompt_request(NonSpineLLMRuntimeRequest(user_input="hi"))
        comp = adapter.complete(pr)
        self.assertEqual(len(calls), 1)
        self.assertIsInstance(calls[0], NonSpineLLMProviderRequest)
        self.assertIsInstance(comp, NonSpineLLMCompletion)
        self.assertEqual(comp.text, "spy text")

    def test_default_completion_path_uses_fake_provider(self):
        pr = NonSpineLLMRuntime._build_prompt_request(NonSpineLLMRuntimeRequest(user_input="hi"))
        comp = FakeNonSpineLLMCompletionAdapter().complete(pr)
        self.assertIsInstance(comp, NonSpineLLMCompletion)
        self.assertIs(comp.is_fake, True)
        self.assertIs(comp.provider_called, False)
        self.assertIn("fake no-op", comp.text)


class TestPromptRequestPackage(unittest.TestCase):
    def test_prompt_request_is_dataclass(self):
        self.assertIsInstance(NonSpineLLMPromptRequest, type)
        self.assertTrue(dataclasses.is_dataclass(NonSpineLLMPromptRequest))

    def test_build_prompt_request_returns_package(self):
        req = NonSpineLLMRuntimeRequest(user_input="hi", system_text="sys", extra_messages=("m1",))
        pr = NonSpineLLMRuntime._build_prompt_request(req)
        self.assertIsInstance(pr, NonSpineLLMPromptRequest)
        self.assertIsInstance(pr.system_text, str)
        self.assertIsInstance(pr.rendered_prompt, str)
        self.assertIsInstance(pr.messages, tuple)
        self.assertIn("hi", pr.rendered_prompt)


class TestCompletionAdapters(unittest.TestCase):
    def test_completion_and_adapter_types_exist(self):
        self.assertIsInstance(NonSpineLLMCompletion, type)
        self.assertIsInstance(NonSpineLLMCompletionAdapter, type)
        self.assertIsInstance(FakeNonSpineLLMCompletionAdapter, type)
        self.assertTrue(issubclass(FakeNonSpineLLMCompletionAdapter, NonSpineLLMCompletionAdapter))

    def test_fake_adapter_complete_returns_completion(self):
        pr = NonSpineLLMRuntime._build_prompt_request(NonSpineLLMRuntimeRequest(user_input="hi", system_text="sys"))
        comp = FakeNonSpineLLMCompletionAdapter().complete(pr)
        self.assertIsInstance(comp, NonSpineLLMCompletion)
        self.assertIs(comp.is_fake, True)
        self.assertIs(comp.provider_called, False)

    def test_base_adapter_performs_no_completion(self):
        pr = NonSpineLLMRuntime._build_prompt_request(NonSpineLLMRuntimeRequest(user_input="hi"))
        with self.assertRaises(NotImplementedError):
            NonSpineLLMCompletionAdapter().complete(pr)


class TestRunUsesFakeAdapter(unittest.TestCase):
    def _request(self):
        return NonSpineLLMRuntimeRequest(
            agent_id="agent_x", user_input="hello there", system_text="you are agent_x",
            memory_context_text="remembered detail alpha", extra_messages=("prior turn beta",))

    def test_run_returns_result_type(self):
        self.assertIsInstance(NonSpineLLMRuntime().run(self._request()), NonSpineLLMRuntimeResult)

    def test_result_is_explicitly_fake_no_op(self):
        result = NonSpineLLMRuntime().run(self._request())
        self.assertIs(result.is_fake, True)
        self.assertIs(result.provider_called, False)
        self.assertIn("fake no-op", result.response_text)

    def test_result_carries_fake_completion_and_capture(self):
        result = NonSpineLLMRuntime().run(self._request())
        self.assertIsInstance(result.completion, NonSpineLLMCompletion)
        self.assertIs(result.completion.is_fake, True)
        self.assertIs(result.completion.provider_called, False)
        self.assertEqual(result.response_text, result.completion.text)
        self.assertIsInstance(result.prompt_request, NonSpineLLMPromptRequest)
        self.assertIsInstance(result.prompt_request.memory_context, NonSpineLLMMemoryContext)
        self.assertIn(MEMORY_LABEL, result.rendered_prompt)
        self.assertIn("hello there", result.rendered_prompt)
        self.assertIn("you are agent_x", result.rendered_prompt)
        self.assertIn("remembered detail alpha", result.rendered_prompt)
        self.assertIn("prior turn beta", result.rendered_prompt)

    def test_fake_path_is_deterministic(self):
        req = self._request()
        self.assertEqual(NonSpineLLMRuntime().run(req), NonSpineLLMRuntime().run(req))


class TestForbiddenReferencesAbsent(unittest.TestCase):
    def test_forbidden_substrings_absent(self):
        present = [s for s in FORBIDDEN_SUBSTRINGS if s in MODULE_SRC]
        self.assertEqual(present, [], "forbidden substrings present: %s" % present)

    def test_only_stdlib_imports(self):
        offending = _module_import_roots() - ALLOWED_IMPORT_ROOTS
        self.assertEqual(offending, set(), "non-stdlib imports: %s" % offending)

    def test_no_network_subprocess_sdk_env_imports(self):
        offending = _module_import_roots() & FORBIDDEN_IMPORT_ROOTS
        self.assertEqual(offending, set(), "forbidden imports: %s" % offending)

    def test_complete_call_only_on_local_fake_adapter(self):
        self.assertNotIn(".chat(", MODULE_SRC)
        complete_lines = [ln for ln in MODULE_SRC.splitlines() if ".complete(" in ln]
        self.assertTrue(complete_lines)
        for ln in complete_lines:
            self.assertIn("adapter.complete(", ln, "non-local .complete( call: %s" % ln.strip())

    def test_generate_call_only_on_local_provider_adapter(self):
        generate_lines = [ln for ln in MODULE_SRC.splitlines() if ".generate(" in ln]
        self.assertTrue(generate_lines)
        for ln in generate_lines:
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
        offenders = [str(p.relative_to(REPO_ROOT)) for p, s in self._iter_target_sources() if "non_spine_llm_runtime" in s]
        self.assertEqual(offenders, [], "live wiring found in: %s" % offenders)


class TestSpineLockPresent(unittest.TestCase):
    def test_spine_lock_file_present(self):
        lock = REPO_ROOT / "tests" / "test_spine_cognition_memory_context_characterization_lock.py"
        self.assertTrue(lock.exists())


if __name__ == "__main__":
    unittest.main()
