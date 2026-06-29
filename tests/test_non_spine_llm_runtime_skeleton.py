"""tests/test_non_spine_llm_runtime_skeleton.py

Guards for the dormant, internal, non-Spine LLM runtime skeleton
(``torment_service/non_spine_llm_runtime.py``), including the provider-boundary /
prompt-request package and the bounded, read-only memory-context package.

Proves: the owner / request / memory-context / prompt-request / completion / adapter /
run shape exists; the memory-context package is bounded, read-only, stripped, and capped;
``run(...)`` goes through a deterministic fake, no-provider completion adapter; the
read-only guidance label renders only for non-empty memory; forbidden references and
non-stdlib/network/subprocess/SDK imports are absent; the only ``.complete(`` is the
local fake-adapter call; no live wiring into app / spine / mcp_server / cognition / roles;
and the Spine lock is present. The companion focused command runs the Spine
characterization lock alongside this file to prove it remains green.
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
)

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "torment_service" / "non_spine_llm_runtime.py"
MODULE_SRC = MODULE_PATH.read_text(encoding="utf-8")

MEMORY_LABEL = "MEMORY-CONTEXT (read-only guidance):"

# Substrings that must NOT appear anywhere in the new module source.
# NOTE: ".complete(" is intentionally NOT here -- it is allowed ONLY as the local fake
# adapter call and is checked separately (test_complete_call_only_on_local_fake_adapter).
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
]

# Only these stdlib roots may be imported by the new module.
ALLOWED_IMPORT_ROOTS = {"__future__", "dataclasses", "typing"}

# Import roots that must never appear (network / HTTP / socket / subprocess / SDK / async).
FORBIDDEN_IMPORT_ROOTS = {
    "openai",
    "anthropic",
    "socket",
    "http",
    "urllib",
    "ssl",
    "subprocess",
    "requests",
    "httpx",
    "aiohttp",
    "asyncio",
    "threading",
    "sqlite3",
    "pickle",
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
    """Guard - the named owner / request / prompt-request / result / run shape exists."""

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
    """Guards 1-7 - the bounded, read-only memory-context package."""

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
        # is_governed is a caller-supplied assertion marker; it is just a bool field.
        mc = NonSpineLLMMemoryContext.from_text("m", is_governed=True)
        self.assertIs(mc.is_governed, True)
        self.assertIs(mc.is_read_only, True)


class TestMemoryContextWiring(unittest.TestCase):
    """Guards 8-12 - build/use the package; render label only for non-empty memory."""

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


class TestPromptRequestPackage(unittest.TestCase):
    """Guard - the prompt-request package exists and is primitive/dataclass-shaped."""

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
    """Guard - completion object + adapter base + fake adapter exist and behave."""

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
        # The base seam carries no provider; it performs no completion.
        req = NonSpineLLMRuntimeRequest(user_input="hi")
        pr = NonSpineLLMRuntime._build_prompt_request(req)
        with self.assertRaises(NotImplementedError):
            NonSpineLLMCompletionAdapter().complete(pr)


class TestRunUsesFakeAdapter(unittest.TestCase):
    """Guard 13 - run(...) goes through the fake adapter; explicitly fake / no-op."""

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
        # fake completion data carried
        self.assertIsInstance(result.completion, NonSpineLLMCompletion)
        self.assertIs(result.completion.is_fake, True)
        self.assertIs(result.completion.provider_called, False)
        self.assertEqual(result.response_text, result.completion.text)
        # prompt / request + memory-context capture carried (in-memory, for tests only)
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
    """Guards 14-16 - forbidden references / imports absent; .complete( scoped to fake."""

    def test_forbidden_substrings_absent(self):
        present = [s for s in FORBIDDEN_SUBSTRINGS if s in MODULE_SRC]
        self.assertEqual(present, [], "forbidden substrings present: %s" % present)

    def test_only_stdlib_imports(self):
        offending = _module_import_roots() - ALLOWED_IMPORT_ROOTS
        self.assertEqual(offending, set(), "non-stdlib imports: %s" % offending)

    def test_no_network_subprocess_sdk_imports(self):
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


class TestNoLiveWiring(unittest.TestCase):
    """Guard 17 - no live surface imports or references the new module."""

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
    """Guard 18 - the Spine characterization lock is present.

    Its actual pass/fail is asserted by running it in the focused command alongside
    this file.
    """

    def test_spine_lock_file_present(self):
        lock = (
            REPO_ROOT
            / "tests"
            / "test_spine_cognition_memory_context_characterization_lock.py"
        )
        self.assertTrue(lock.exists())


if __name__ == "__main__":
    unittest.main()
