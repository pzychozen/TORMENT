"""tests/test_non_spine_llm_callable_adapter_harness.py

Guards for the test-only callable-adapter manual harness
(``tests/manual/non_spine_llm_callable_adapter_harness.py``).

Exercises the harness with fake / spy callables only, and asserts the harness imports
nothing beyond the dormant non-Spine runtime + stdlib (no SDK / env / network / secrets;
no app / spine / mcp / cognition / roles surface). The companion focused command runs the
runtime-skeleton guards and the Spine characterization lock to prove they remain green.
"""
import ast
import unittest
from pathlib import Path

from torment_service.non_spine_llm_runtime import (
    NonSpineLLMRuntime,
    NonSpineLLMRuntimeRequest,
    NonSpineLLMRuntimeResult,
    NonSpineLLMPromptRequest,
    NonSpineLLMProviderRequest,
)
from tests.manual.non_spine_llm_callable_adapter_harness import (
    run_non_spine_callable_provider_harness,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
HARNESS_PATH = (
    REPO_ROOT / "tests" / "manual" / "non_spine_llm_callable_adapter_harness.py"
)
HARNESS_SRC = HARNESS_PATH.read_text(encoding="utf-8")

MEMORY_LABEL = "MEMORY-CONTEXT (read-only guidance):"

# The harness may import ONLY these exact modules.
ALLOWED_IMPORT_MODULES = {
    "__future__",
    "typing",
    "torment_service.non_spine_llm_runtime",
}

# Tokens that must never appear in the harness source. (Deliberately excludes generic
# words like "app"/"spine"/"roles" that are substrings of the legitimate
# `non_spine_llm_runtime` import / NonSpine* class names; module-level forbidden refs are
# covered by the import allowlist instead.)
CURATED_FORBIDDEN_SUBSTRINGS = [
    "openai",
    "anthropic",
    "requests",
    "httpx",
    "urllib",
    "socket",
    "ssl",
    "os.environ",
    "os.getenv",
    "getenv(",
    "dotenv",
    "subprocess",
    "asyncio",
    "threading",
    ".chat(",
    "AgentRunner",
    "agent_loop",
    "memory_context_orchestrator",
    "retrieval_assembler",
    "assemble_context",
    "AssembledContext",
    "TormentFabric",
    "FastAPI",
    "@mcp.tool",
]


def _harness_import_modules():
    mods = set()
    for node in ast.walk(ast.parse(HARNESS_SRC)):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mods.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            mods.add(node.module or "")
    return mods


class TestCallableAdapterHarness(unittest.TestCase):
    """Guards 1-8 - the harness drives the callable adapter end-to-end (fake callables)."""

    def _run(self, completion_callable, **kw):
        return run_non_spine_callable_provider_harness(completion_callable, **kw)

    def test_harness_returns_runtime_result(self):
        res = self._run(lambda request: "manual out", user_input="hi")
        self.assertIsInstance(res, NonSpineLLMRuntimeResult)

    def test_injected_callable_receives_provider_request(self):
        seen = []

        def _cb(request):
            seen.append(request)
            return "manual out"

        self._run(_cb, user_input="hi")
        self.assertEqual(len(seen), 1)
        self.assertIsInstance(seen[0], NonSpineLLMProviderRequest)

    def test_result_carries_callable_text(self):
        res = self._run(lambda request: "callable says hi", user_input="hi")
        self.assertEqual(res.response_text, "callable says hi")
        self.assertEqual(res.completion.text, "callable says hi")

    def test_result_provider_called_true(self):
        res = self._run(lambda request: "x", user_input="hi")
        self.assertIs(res.provider_called, True)

    def test_result_is_not_fake(self):
        res = self._run(lambda request: "x", user_input="hi")
        self.assertIs(res.is_fake, False)

    def test_result_carries_prompt_capture(self):
        res = self._run(
            lambda request: "x", user_input="hello there", system_text="sys"
        )
        self.assertIsInstance(res.prompt_request, NonSpineLLMPromptRequest)
        self.assertIn("USER: hello there", res.rendered_prompt)
        self.assertIn("SYSTEM: sys", res.rendered_prompt)

    def test_memory_context_renders_through_label(self):
        res = self._run(
            lambda request: "x",
            user_input="hi",
            memory_context_text="remember me",
        )
        self.assertIn(MEMORY_LABEL, res.rendered_prompt)
        self.assertIn("remember me", res.rendered_prompt)

    def test_default_runtime_path_remains_fake(self):
        runtime = NonSpineLLMRuntime()
        result = runtime.run(NonSpineLLMRuntimeRequest(user_input="hi"))
        self.assertIs(result.is_fake, True)
        self.assertIs(result.provider_called, False)
        self.assertIn("fake no-op", result.response_text)


class TestHarnessForbiddenImports(unittest.TestCase):
    """Guards 9-10 - the harness imports/references nothing forbidden."""

    def test_harness_imports_allowlisted_only(self):
        mods = _harness_import_modules()
        offending = mods - ALLOWED_IMPORT_MODULES
        self.assertEqual(offending, set(), "unexpected harness imports: %s" % offending)

    def test_harness_no_forbidden_substrings(self):
        present = [s for s in CURATED_FORBIDDEN_SUBSTRINGS if s in HARNESS_SRC]
        self.assertEqual(present, [], "forbidden substrings in harness: %s" % present)


if __name__ == "__main__":
    unittest.main()
