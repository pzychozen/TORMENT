"""tests/test_non_spine_llm_character_operator_harness.py

Guards for the manual character-shaped operator harness
(``tests/manual/non_spine_llm_character_operator_harness.py``).

The default path is fake / no-provider (no env, no SDK, no network). The opt-in real path
is exercised with a FAKE env mapping + FAKE/spy SDK factory only -- no real env, no SDK
install, no network, no real provider call. The CLI's pytest-refusal of the real path is
exercised by simulating ``pytest`` in ``sys.modules``. The harness imports are checked
(stdlib + the non-Spine runtime only) and the source is scanned for forbidden tokens /
file writes / character-production references.
"""
import ast
import sys
import unittest
from pathlib import Path

import tests.manual.non_spine_llm_character_operator_harness as harness
from tests.manual.non_spine_llm_character_operator_harness import (
    NonSpineLLMCharacterHarnessRequest,
    build_non_spine_character_runtime_request,
    run_non_spine_character_operator_harness,
    main,
)
from torment_service.non_spine_llm_runtime import (
    NonSpineLLMRuntimeRequest,
    NonSpineLLMRuntimeResult,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
HARNESS_PATH = (
    REPO_ROOT / "tests" / "manual" / "non_spine_llm_character_operator_harness.py"
)
HARNESS_SRC = HARNESS_PATH.read_text(encoding="utf-8")

GATE = "TORMENT_NON_SPINE_LLM_REAL_PROVIDER"
KEY = "ANTHROPIC_API_KEY"
MODEL = "TORMENT_NON_SPINE_ANTHROPIC_MODEL"

MEMORY_LABEL = "MEMORY-CONTEXT (read-only guidance):"

ALLOWED_IMPORT_MODULES = {
    "__future__",
    "argparse",
    "sys",
    "dataclasses",
    "typing",
    "torment_service.non_spine_llm_runtime",
}

CURATED_FORBIDDEN_SUBSTRINGS = [
    "torment_service.character", "CharacterStore", "TormentFabric",
    "assemble_context", "AssembledContext", "retrieval_assembler",
    "memory_context_orchestrator", "AgentRunner", "agent_loop", "FastAPI",
    "@mcp.tool", "mcp_server", "openai", "requests", "httpx", "urllib", "socket",
    "ssl", "subprocess", "dotenv", "open(", ".write(", "logging", ".chat(",
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
    def __init__(self, blocks=None):
        self.called = 0
        self.blocks = blocks if blocks is not None else [_FakeBlock("hi from fake")]

    def __call__(self):
        self.called += 1
        factory = self

        class _Messages:
            def create(self, **kwargs):
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
    def test_file_exists(self):
        self.assertTrue(HARNESS_PATH.exists())

    def test_names_exist(self):
        self.assertIsInstance(NonSpineLLMCharacterHarnessRequest, type)
        self.assertTrue(callable(build_non_spine_character_runtime_request))
        self.assertTrue(callable(run_non_spine_character_operator_harness))
        self.assertTrue(callable(main))


class TestBuildSafeSeam(unittest.TestCase):
    def test_builds_plain_runtime_request_from_character_fields(self):
        req = NonSpineLLMCharacterHarnessRequest(
            character_id="ryuki_01", character_name="Ryuki", seed_text="terse, dry",
            user_input="hello", memory_context_text="prefers brevity",
            extra_messages=("prior turn",))
        rt = build_non_spine_character_runtime_request(req)
        self.assertIsInstance(rt, NonSpineLLMRuntimeRequest)
        self.assertEqual(rt.user_input, "hello")
        self.assertEqual(rt.agent_id, "ryuki_01")
        self.assertIn("Ryuki", rt.system_text)
        self.assertIn("ryuki_01", rt.system_text)
        self.assertIn("terse, dry", rt.system_text)
        self.assertEqual(rt.memory_context_text, "prefers brevity")
        self.assertEqual(rt.extra_messages, ("prior turn",))


class TestDefaultFakePath(unittest.TestCase):
    def test_default_path_is_fake_no_provider(self):
        req = NonSpineLLMCharacterHarnessRequest(
            character_name="Ryuki", seed_text="terse", user_input="hello",
            memory_context_text="remember brevity")
        res = run_non_spine_character_operator_harness(req)  # no env, no real provider
        self.assertIsInstance(res, NonSpineLLMRuntimeResult)
        self.assertIs(res.is_fake, True)
        self.assertIs(res.provider_called, False)
        self.assertIn("fake no-op", res.response_text)

    def test_character_fields_flow_into_rendered_prompt(self):
        req = NonSpineLLMCharacterHarnessRequest(
            character_name="Ryuki", seed_text="terse, dry", user_input="hello there",
            memory_context_text="remember brevity")
        res = run_non_spine_character_operator_harness(req)
        self.assertIn("SYSTEM: You are Ryuki", res.rendered_prompt)
        self.assertIn("terse, dry", res.rendered_prompt)
        self.assertIn("USER: hello there", res.rendered_prompt)
        self.assertIn(MEMORY_LABEL, res.rendered_prompt)
        self.assertIn("remember brevity", res.rendered_prompt)


class TestRealPathMockedOnly(unittest.TestCase):
    def test_real_path_uses_fake_sdk_and_returns_real_markers(self):
        req = NonSpineLLMCharacterHarnessRequest(character_name="Ryuki", user_input="hi")
        spy = _SpySdkFactory(blocks=[_FakeBlock("hello from anthropic-fake")])
        res = run_non_spine_character_operator_harness(
            req, use_real_anthropic=True, env=_valid_env(), sdk_factory=spy)
        self.assertIsInstance(res, NonSpineLLMRuntimeResult)
        self.assertIs(res.provider_called, True)
        self.assertIs(res.is_fake, False)
        self.assertEqual(res.response_text, "hello from anthropic-fake")
        self.assertEqual(spy.called, 1)

    def test_does_not_echo_or_return_api_key(self):
        secret = "sk-DO-NOT-LEAK-SECRET"
        req = NonSpineLLMCharacterHarnessRequest(
            character_name="Ryuki", seed_text="sd", user_input="hi",
            memory_context_text="mem")
        spy = _SpySdkFactory(blocks=[_FakeBlock("ok")])
        res = run_non_spine_character_operator_harness(
            req, use_real_anthropic=True, env=_valid_env(**{KEY: secret}), sdk_factory=spy)
        for value in (res.response_text, res.rendered_prompt, res.completion.text,
                      res.completion.echoed_prompt, res.prompt_request.rendered_prompt):
            self.assertNotIn("SECRET", value)
            self.assertNotIn(secret, value)


class TestCliRefusesRealUnderPytest(unittest.TestCase):
    def test_cli_refuses_real_anthropic_when_pytest_present(self):
        had = "pytest" in sys.modules
        if not had:
            sys.modules["pytest"] = object()
        try:
            self.assertEqual(main(["--real-anthropic", "--user-input", "hi"]), 2)
        finally:
            if not had:
                del sys.modules["pytest"]

    def test_default_cli_fake_path_runs_without_real(self):
        # Default (no --real-anthropic) is the fake path; succeeds even with pytest present.
        self.assertEqual(main(["--user-input", "hi", "--character-name", "Ryuki"]), 0)


class TestHarnessImportsAndForbidden(unittest.TestCase):
    def test_imports_allowlisted_only(self):
        offending = _harness_import_modules() - ALLOWED_IMPORT_MODULES
        self.assertEqual(offending, set(), "unexpected harness imports: %s" % offending)

    def test_no_forbidden_substrings(self):
        present = [s for s in CURATED_FORBIDDEN_SUBSTRINGS if s in HARNESS_SRC]
        self.assertEqual(present, [], "forbidden substrings in harness: %s" % present)


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

    def test_no_reference_to_harness_or_runtime(self):
        offenders = []
        for path, src in self._iter_target_sources():
            if ("non_spine_llm_runtime" in src
                    or "non_spine_llm_character_operator_harness" in src):
                offenders.append(str(path.relative_to(REPO_ROOT)))
        self.assertEqual(offenders, [], "live wiring found in: %s" % offenders)


if __name__ == "__main__":
    unittest.main()
