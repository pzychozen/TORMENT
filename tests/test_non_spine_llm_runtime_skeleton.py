"""tests/test_non_spine_llm_runtime_skeleton.py

Guards for the dormant, internal, non-Spine LLM runtime skeleton
(``torment_service/non_spine_llm_runtime.py``), including the provider-boundary /
prompt-request package.

Proves: the owner / request / prompt-request / completion / adapter / run shape exists;
``run(...)`` goes through a deterministic fake, no-provider completion adapter; forbidden
references and non-stdlib/network/subprocess/SDK imports are absent from the module; the
only ``.complete(`` is the local fake-adapter call; no live wiring into
app / spine / mcp_server / cognition / roles; and the Spine lock is present. The companion
focused command runs the Spine characterization lock alongside this file to prove it
remains green.
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
)

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "torment_service" / "non_spine_llm_runtime.py"
MODULE_SRC = MODULE_PATH.read_text(encoding="utf-8")

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
    """Guard 1 - the named owner / request / prompt-request / result / run shape exists."""

    def test_runtime_class_exists(self):
        self.assertTrue(hasattr(nslr, "NonSpineLLMRuntime"))
        self.assertIsInstance(NonSpineLLMRuntime, type)

    def test_request_and_result_exist(self):
        self.assertIsInstance(NonSpineLLMRuntimeRequest, type)
        self.assertIsInstance(NonSpineLLMRuntimeResult, type)

    def test_run_and_build_prompt_request_callable(self):
        self.assertTrue(callable(getattr(NonSpineLLMRuntime, "run", None)))
        self.assertTrue(callable(getattr(NonSpineLLMRuntime, "_build_prompt_request", None)))


class TestPromptRequestPackage(unittest.TestCase):
    """Guard 1 - the prompt-request package exists and is primitive/dataclass-shaped."""

    def test_prompt_request_is_dataclass(self):
        self.assertIsInstance(NonSpineLLMPromptRequest, type)
        self.assertTrue(dataclasses.is_dataclass(NonSpineLLMPromptRequest))

    def test_build_prompt_request_returns_package(self):
        req = NonSpineLLMRuntimeRequest(
            user_input="hi", system_text="sys", extra_messages=("m1",)
        )
        pr = NonSpineLLMRuntime._build_prompt_request(req)
        self.assertIsInstance(pr, NonSpineLLMPromptRequest)
        # primitive-shaped fields only
        self.assertIsInstance(pr.system_text, str)
        self.assertIsInstance(pr.rendered_prompt, str)
        self.assertIsInstance(pr.messages, tuple)
        self.assertIn("hi", pr.rendered_prompt)


class TestCompletionAdapters(unittest.TestCase):
    """Guard 2 - completion object + adapter base + fake adapter exist and behave."""

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
    """Guard 3 - run(...) goes through the fake adapter; explicitly fake / no-op."""

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
        # prompt / request capture carried (in-memory, for tests only)
        self.assertIsInstance(result.prompt_request, NonSpineLLMPromptRequest)
        self.assertIn("hello there", result.rendered_prompt)
        self.assertIn("hello there", result.prompt_request.rendered_prompt)
        self.assertIn("you are agent_x", result.rendered_prompt)
        self.assertIn("remembered detail alpha", result.rendered_prompt)
        self.assertIn("prior turn beta", result.rendered_prompt)

    def test_fake_path_is_deterministic(self):
        runtime = NonSpineLLMRuntime()
        req = self._request()
        self.assertEqual(runtime.run(req), runtime.run(req))


class TestForbiddenReferencesAbsent(unittest.TestCase):
    """Guard 4 - forbidden references / imports absent; .complete( scoped to fake."""

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
    """Guard 5 - no live surface imports or references the new module."""

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
    """Guard 6 - the Spine characterization lock is present.

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
