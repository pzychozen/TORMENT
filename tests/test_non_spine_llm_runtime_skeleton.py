"""tests/test_non_spine_llm_runtime_skeleton.py

Guards for the dormant, internal, non-Spine LLM runtime skeleton
(``torment_service/non_spine_llm_runtime.py``): the bounded memory-context package, the
prompt-request / completion boundary, the provider-adapter readiness contracts, and the
callable-only MANUAL provider adapter.

Everything is fake / dormant / test-called only (the callable adapter is exercised solely
with fake / spy callables). The companion focused command runs the Spine characterization
lock alongside this file to prove it remains green.
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
)

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "torment_service" / "non_spine_llm_runtime.py"
MODULE_SRC = MODULE_PATH.read_text(encoding="utf-8")

MEMORY_LABEL = "MEMORY-CONTEXT (read-only guidance):"

FORBIDDEN_SUBSTRINGS = [
    "FastAPI",
    "@mcp.tool",
    "run_cognition_pipeline",
    "AgentRunner",
    "run_turn",
    "memory_context_orchestrator",
    "assemble_context",
    "AssembledContext",
    "retrieval_assembler",
    "TormentFabric",
    "openai",
    "anthropic",
    ".chat(",
    "ingest",
    "reinforce",
    "promote",
    "write",
    "transcript",
    "scheduler",
    "create_task",
    "Thread",
    "subprocess",
    "socket",
    "os.environ",
    "os.getenv",
    "getenv(",
    "dotenv",
]

ALLOWED_IMPORT_ROOTS = {"__future__", "dataclasses", "typing"}

FORBIDDEN_IMPORT_ROOTS = {
    "openai",
    "anthropic",
    "socket",
    "ssl",
    "http",
    "urllib",
    "subprocess",
    "requests",
    "httpx",
    "aiohttp",
    "asyncio",
    "threading",
    "sqlite3",
    "pickle",
    "os",
    "secrets",
    "dotenv",
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
        req = NonSpineLLMRuntimeRequest(
            user_input="hi", memory_context_text="remembered alpha"
        )
        pr = NonSpineLLMRuntime._build_prompt_request(req)
        self.assertIsInstance(pr, NonSpineLLMPromptRequest)
        self.assertIsInstance(pr.memory_context, NonSpineLLMMemoryContext)
        self.assertEqual(pr.memory_context.text, "remembered alpha")

    def test_rendered_prompt_includes_label_for_nonempty_memory(self):
        req = NonSpineLLMRuntimeRequest(
            user_input="hi", memory_context_text="remembered alpha"
        )
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
        for cls in (
            NonSpineLLMProviderConfig,
            NonSpineLLMProviderRequest,
            NonSpineLLMProviderResult,
            NonSpineLLMProviderAdapter,
            FakeNonSpineLLMProviderAdapter,
        ):
            self.assertIsInstance(cls, type)

    def test_config_request_result_are_frozen_dataclasses(self):
        for cls in (
            NonSpineLLMProviderConfig,
            NonSpineLLMProviderRequest,
            NonSpineLLMProviderResult,
        ):
            self.assertTrue(dataclasses.is_dataclass(cls))
            self.assertTrue(cls.__dataclass_params__.frozen)

    def test_config_and_result_are_primitive_shaped(self):
        cfg = NonSpineLLMProviderConfig()
        for value in (cfg.provider_name, cfg.model_name):
            self.assertIsInstance(value, str)
        for value in (cfg.is_fake, cfg.network_enabled):
            self.assertIsInstance(value, bool)
        res = FakeNonSpineLLMProviderAdapter().generate(
            NonSpineLLMProviderRequest(prompt_request=NonSpineLLMPromptRequest())
        )
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
            prompt_request=NonSpineLLMPromptRequest(rendered_prompt="USER: hi")
        )
        adapter = FakeNonSpineLLMProviderAdapter()
        r1 = adapter.generate(req)
        r2 = adapter.generate(req)
        self.assertIsInstance(r1, NonSpineLLMProviderResult)
        self.assertEqual(r1, r2)

    def test_fake_provider_result_markers(self):
        req = NonSpineLLMProviderRequest(prompt_request=NonSpineLLMPromptRequest())
        res = FakeNonSpineLLMProviderAdapter().generate(req)
        self.assertIs(res.is_fake, True)
        self.assertIs(res.provider_called, False)


class TestCallableProviderAdapter(unittest.TestCase):
    """Guards 1-9, 12 - the callable-only MANUAL provider adapter (fake/spy callables)."""

    def _req(self, rendered="USER: hi"):
        return NonSpineLLMProviderRequest(
            prompt_request=NonSpineLLMPromptRequest(rendered_prompt=rendered)
        )

    def test_exists_and_subclasses_provider_adapter(self):
        self.assertIsInstance(CallableNonSpineLLMProviderAdapter, type)
        self.assertTrue(
            issubclass(CallableNonSpineLLMProviderAdapter, NonSpineLLMProviderAdapter)
        )

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

        adapter = CallableNonSpineLLMProviderAdapter(_cb)
        adapter.generate(self._req())
        self.assertEqual(len(seen), 1)
        self.assertIsInstance(seen[0], NonSpineLLMProviderRequest)

    def test_converts_string_output_to_result_with_markers(self):
        adapter = CallableNonSpineLLMProviderAdapter(lambda request: "manual text")
        res = adapter.generate(self._req("USER: hi"))
        self.assertIsInstance(res, NonSpineLLMProviderResult)
        self.assertEqual(res.text, "manual text")
        self.assertIs(res.provider_called, True)
        self.assertIs(res.is_fake, False)
        self.assertEqual(res.echoed_prompt, "USER: hi")

    def test_coerces_non_string_output_to_str(self):
        adapter = CallableNonSpineLLMProviderAdapter(lambda request: 123)
        res = adapter.generate(self._req())
        self.assertIsInstance(res.text, str)
        self.assertEqual(res.text, "123")

    def test_deterministic_when_callable_deterministic(self):
        adapter = CallableNonSpineLLMProviderAdapter(lambda request: "stable")
        self.assertEqual(adapter.generate(self._req()), adapter.generate(self._req()))

    def test_callable_adapter_only_in_its_class_definition(self):
        # Guard 12: the callable adapter is never instantiated or referenced in the
        # module outside its own class definition (so no default path can use it).
        lines = [
            ln for ln in MODULE_SRC.splitlines()
            if "CallableNonSpineLLMProviderAdapter" in ln
        ]
        self.assertTrue(lines, "CallableNonSpineLLMProviderAdapter must be defined")
        for ln in lines:
            self.assertTrue(
                ln.lstrip().startswith("class CallableNonSpineLLMProviderAdapter"),
                "referenced outside its class definition: %s" % ln.strip(),
            )


class TestCompletionDelegatesToProvider(unittest.TestCase):
    def test_completion_adapter_delegates_to_provider(self):
        calls = []

        class _SpyProvider(NonSpineLLMProviderAdapter):
            def generate(self, request):
                calls.append(request)
                return NonSpineLLMProviderResult(
                    text="spy text",
                    is_fake=True,
                    provider_called=False,
                    provider_name=request.config.provider_name,
                    model_name=request.config.model_name,
                    echoed_prompt=request.prompt_request.rendered_prompt,
                )

        adapter = FakeNonSpineLLMCompletionAdapter(provider_adapter=_SpyProvider())
        pr = NonSpineLLMRuntime._build_prompt_request(
            NonSpineLLMRuntimeRequest(user_input="hi")
        )
        comp = adapter.complete(pr)
        self.assertEqual(len(calls), 1)
        self.assertIsInstance(calls[0], NonSpineLLMProviderRequest)
        self.assertIsInstance(comp, NonSpineLLMCompletion)
        self.assertEqual(comp.text, "spy text")

    def test_default_completion_path_uses_fake_provider(self):
        pr = NonSpineLLMRuntime._build_prompt_request(
            NonSpineLLMRuntimeRequest(user_input="hi")
        )
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
        req = NonSpineLLMRuntimeRequest(
            user_input="hi", system_text="sys", extra_messages=("m1",)
        )
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
        self.assertTrue(
            issubclass(FakeNonSpineLLMCompletionAdapter, NonSpineLLMCompletionAdapter)
        )

    def test_fake_adapter_complete_returns_completion(self):
        req = NonSpineLLMRuntimeRequest(user_input="hi", system_text="sys")
        pr = NonSpineLLMRuntime._build_prompt_request(req)
        comp = FakeNonSpineLLMCompletionAdapter().complete(pr)
        self.assertIsInstance(comp, NonSpineLLMCompletion)
        self.assertIs(comp.is_fake, True)
        self.assertIs(comp.provider_called, False)

    def test_base_adapter_performs_no_completion(self):
        req = NonSpineLLMRuntimeRequest(user_input="hi")
        pr = NonSpineLLMRuntime._build_prompt_request(req)
        with self.assertRaises(NotImplementedError):
            NonSpineLLMCompletionAdapter().complete(pr)


class TestRunUsesFakeAdapter(unittest.TestCase):
    def _request(self):
        return NonSpineLLMRuntimeRequest(
            agent_id="agent_x",
            user_input="hello there",
            system_text="you are agent_x",
            memory_context_text="remembered detail alpha",
            extra_messages=("prior turn beta",),
        )

    def test_run_returns_result_type(self):
        runtime = NonSpineLLMRuntime()
        result = runtime.run(self._request())
        self.assertIsInstance(result, NonSpineLLMRuntimeResult)

    def test_result_is_explicitly_fake_no_op(self):
        runtime = NonSpineLLMRuntime()
        result = runtime.run(self._request())
        self.assertIs(result.is_fake, True)
        self.assertIs(result.provider_called, False)
        self.assertIn("fake no-op", result.response_text)

    def test_result_carries_fake_completion_and_capture(self):
        runtime = NonSpineLLMRuntime()
        result = runtime.run(self._request())
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
        runtime = NonSpineLLMRuntime()
        req = self._request()
        self.assertEqual(runtime.run(req), runtime.run(req))


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
        self.assertTrue(
            complete_lines, "expected exactly the local fake-adapter .complete( call"
        )
        for ln in complete_lines:
            self.assertIn(
                "adapter.complete(",
                ln,
                "non-local provider-style .complete( call: %s" % ln.strip(),
            )

    def test_generate_call_only_on_local_provider_adapter(self):
        generate_lines = [ln for ln in MODULE_SRC.splitlines() if ".generate(" in ln]
        self.assertTrue(
            generate_lines, "expected the local provider .generate( call"
        )
        for ln in generate_lines:
            self.assertIn(
                "provider_adapter.generate(",
                ln,
                "non-local .generate( call: %s" % ln.strip(),
            )


class TestNoLiveWiring(unittest.TestCase):
    def _iter_target_sources(self):
        targets = [
            REPO_ROOT / "torment_service" / "app.py",
            REPO_ROOT / "torment_service" / "spine.py",
            REPO_ROOT / "torment_service" / "mcp_server.py",
        ]
        for pkg in ("cognition", "roles"):
            targets.extend(sorted((REPO_ROOT / pkg).glob("*.py")))
        for path in targets:
            if path.exists():
                yield path, path.read_text(encoding="utf-8")

    def test_no_reference_to_new_module(self):
        offenders = []
        for path, src in self._iter_target_sources():
            if "non_spine_llm_runtime" in src:
                offenders.append(str(path.relative_to(REPO_ROOT)))
        self.assertEqual(offenders, [], "live wiring found in: %s" % offenders)


class TestSpineLockPresent(unittest.TestCase):
    def test_spine_lock_file_present(self):
        lock = (
            REPO_ROOT
            / "tests"
            / "test_spine_cognition_memory_context_characterization_lock.py"
        )
        self.assertTrue(lock.exists())


if __name__ == "__main__":
    unittest.main()
