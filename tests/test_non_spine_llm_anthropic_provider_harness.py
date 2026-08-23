"""tests/test_non_spine_llm_anthropic_provider_harness.py

Guards for the operator / manual Anthropic provider harness
(``tests/manual/non_spine_llm_anthropic_provider_harness.py``).

All tests use a FAKE env mapping plus a FAKE / spy SDK factory only -- no real env lookup,
no SDK install, no network, no real provider call. The CLI's pytest-refusal is exercised by
simulating ``pytest`` in ``sys.modules``. The harness imports are checked (stdlib + the
non-Spine runtime only) and the source is scanned for forbidden tokens / file writes.
"""
import ast
import sys
import unittest
from pathlib import Path

from torment_service.non_spine_llm_runtime import (
    NonSpineLLMRuntimeResult,
    NonSpineLLMRealProviderError,
)
from tests.manual.non_spine_llm_anthropic_provider_harness import (
    run_non_spine_anthropic_provider_harness,
    main,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
HARNESS_PATH = (
    REPO_ROOT / "tests" / "manual" / "non_spine_llm_anthropic_provider_harness.py"
)
HARNESS_SRC = HARNESS_PATH.read_text(encoding="utf-8")

GATE = "TORMENT_NON_SPINE_LLM_REAL_PROVIDER"
KEY = "ANTHROPIC_API_KEY"
MODEL = "TORMENT_NON_SPINE_ANTHROPIC_MODEL"

ALLOWED_IMPORT_MODULES = {
    "__future__",
    "argparse",
    "sys",
    "typing",
    "torment_service.non_spine_llm_runtime",
}

CURATED_FORBIDDEN_SUBSTRINGS = [
    "openai", "requests", "httpx", "urllib", "socket", "ssl", "subprocess",
    "dotenv", "asyncio", "threading", ".chat(", "AgentRunner", "agent_loop",
    "memory_context_orchestrator", "retrieval_assembler", "assemble_context",
    "AssembledContext", "TormentFabric", "FastAPI", "@mcp.tool",
    "open(", ".write(",
]


def _valid_env(**over):
    env = {GATE: "1", KEY: "sk-fake", MODEL: "claude-fake"}
    env.update(over)
    return env


class _FakeBlock:
    def __init__(self, text):
        self.text = text


class _FakeResponse:
    def __init__(self, blocks):
        self.content = blocks


class _SpySdkFactory:
    def __init__(self, blocks=None, raises_on_create=None):
        self.called = 0
        self.blocks = blocks if blocks is not None else [_FakeBlock("hi from fake")]
        self.raises_on_create = raises_on_create

    def __call__(self):
        self.called += 1
        factory = self

        class _Messages:
            def create(self, **kwargs):
                if factory.raises_on_create is not None:
                    raise factory.raises_on_create
                return _FakeResponse(factory.blocks)

        class _Client:
            def __init__(self, **kwargs):
                self.messages = _Messages()

        class _Module:
            Anthropic = _Client

        return _Module


def _harness_import_modules():
    mods = set()
    for node in ast.walk(ast.parse(HARNESS_SRC)):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mods.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            mods.add(node.module or "")
    return mods


class TestHarnessShape(unittest.TestCase):
    def test_harness_file_exists(self):
        self.assertTrue(HARNESS_PATH.exists())

    def test_helper_and_main_exist(self):
        self.assertTrue(callable(run_non_spine_anthropic_provider_harness))
        self.assertTrue(callable(main))


class TestHarnessImportsAndForbidden(unittest.TestCase):
    def test_imports_allowlisted_only(self):
        offending = _harness_import_modules() - ALLOWED_IMPORT_MODULES
        self.assertEqual(offending, set(), "unexpected harness imports: %s" % offending)

    def test_no_forbidden_substrings(self):
        present = [s for s in CURATED_FORBIDDEN_SUBSTRINGS if s in HARNESS_SRC]
        self.assertEqual(present, [], "forbidden substrings in harness: %s" % present)


class TestCliRefusesUnderPytest(unittest.TestCase):
    def test_cli_refuses_when_pytest_in_sys_modules(self):
        had_pytest = "pytest" in sys.modules
        if not had_pytest:
            sys.modules["pytest"] = object()
        try:
            self.assertEqual(main([]), 2)
        finally:
            if not had_pytest:
                del sys.modules["pytest"]


class TestHelperFailClosed(unittest.TestCase):
    def test_missing_gate_fails_closed(self):
        spy = _SpySdkFactory()
        with self.assertRaises(NonSpineLLMRealProviderError):
            run_non_spine_anthropic_provider_harness(user_input="hi", env={}, sdk_factory=spy)
        self.assertEqual(spy.called, 0)

    def test_missing_key_fails_closed(self):
        spy = _SpySdkFactory()
        with self.assertRaises(NonSpineLLMRealProviderError):
            run_non_spine_anthropic_provider_harness(
                user_input="hi", env={GATE: "1", MODEL: "m"}, sdk_factory=spy)
        self.assertEqual(spy.called, 0)

    def test_missing_model_fails_closed(self):
        spy = _SpySdkFactory()
        with self.assertRaises(NonSpineLLMRealProviderError):
            run_non_spine_anthropic_provider_harness(
                user_input="hi", env={GATE: "1", KEY: "k"}, sdk_factory=spy)
        self.assertEqual(spy.called, 0)


class TestHelperSuccess(unittest.TestCase):
    def test_success_uses_fake_sdk_and_returns_result(self):
        spy = _SpySdkFactory(blocks=[_FakeBlock("hello from anthropic-fake")])
        res = run_non_spine_anthropic_provider_harness(
            user_input="hi", env=_valid_env(), sdk_factory=spy)
        self.assertIsInstance(res, NonSpineLLMRuntimeResult)
        self.assertIs(res.provider_called, True)
        self.assertIs(res.is_fake, False)
        self.assertEqual(res.response_text, "hello from anthropic-fake")
        self.assertEqual(spy.called, 1)

    def test_harness_does_not_echo_or_return_api_key(self):
        secret = "sk-DO-NOT-LEAK-SECRET"
        spy = _SpySdkFactory(blocks=[_FakeBlock("ok")])
        res = run_non_spine_anthropic_provider_harness(
            user_input="hi", system_text="sys", memory_context_text="mem",
            env=_valid_env(**{KEY: secret}), sdk_factory=spy)
        haystacks = (
            res.response_text,
            res.rendered_prompt,
            res.completion.text,
            res.completion.echoed_prompt,
            res.prompt_request.rendered_prompt,
        )
        for value in haystacks:
            self.assertNotIn("SECRET", value)
            self.assertNotIn(secret, value)


if __name__ == "__main__":
    unittest.main()
