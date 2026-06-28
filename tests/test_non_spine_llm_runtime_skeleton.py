"""tests/test_non_spine_llm_runtime_skeleton.py

Guards for the dormant, internal, non-Spine LLM runtime skeleton
(``torment_service/non_spine_llm_runtime.py``).

Proves: the owner/request/result/run shape exists; fake / no-provider behavior;
forbidden references and non-stdlib imports are absent from the module; no live wiring
into app / spine / mcp_server / cognition / roles; and the Spine lock is present. The
companion focused command runs the Spine characterization lock alongside this file to
prove it remains green.
"""
import ast
import unittest
from pathlib import Path

import torment_service.non_spine_llm_runtime as nslr
from torment_service.non_spine_llm_runtime import (
    NonSpineLLMRuntime,
    NonSpineLLMRuntimeRequest,
    NonSpineLLMRuntimeResult,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "torment_service" / "non_spine_llm_runtime.py"
MODULE_SRC = MODULE_PATH.read_text(encoding="utf-8")

# Substrings that must NOT appear anywhere in the new module source.
FORBIDDEN_SUBSTRINGS = [
    "FastAPI",
    "@mcp.tool",
    "run_cognition_pipeline",
    "AgentRunner",
    "run_turn",
    "memory_context_orchestrator",
    "assemble_context",
    "AssembledContext",
    "openai",
    "anthropic",
    ".complete(",
    ".chat(",
    "ingest",
    "reinforce",
    "promote",
    "write",
    "transcript",
    "scheduler",
    "create_task",
    "Thread",
]

# Only these stdlib roots may be imported by the new module.
ALLOWED_IMPORT_ROOTS = {"__future__", "dataclasses", "typing"}


class TestModuleShape(unittest.TestCase):
    """Guard 1 - the named owner / request / result / run shape exists."""

    def test_runtime_class_exists(self):
        self.assertTrue(hasattr(nslr, "NonSpineLLMRuntime"))
        self.assertIsInstance(NonSpineLLMRuntime, type)

    def test_request_and_result_exist(self):
        self.assertIsInstance(NonSpineLLMRuntimeRequest, type)
        self.assertIsInstance(NonSpineLLMRuntimeResult, type)

    def test_run_is_callable(self):
        self.assertTrue(callable(getattr(NonSpineLLMRuntime, "run", None)))


class TestFakeNoProviderBehavior(unittest.TestCase):
    """Guard 2 - direct call returns an explicitly fake / no-op result."""

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
        # The response text is a fixed marker, not model output.
        self.assertIn("fake no-op", result.response_text)

    def test_prompt_capture_is_in_memory_only(self):
        req = self._request()
        runtime = NonSpineLLMRuntime()
        result = runtime.run(req)
        # Prompt-shaped capture data is present only on the returned object.
        self.assertIn("hello there", result.rendered_prompt)
        self.assertIn("you are agent_x", result.rendered_prompt)
        self.assertIn("remembered detail alpha", result.rendered_prompt)
        self.assertIn("prior turn beta", result.rendered_prompt)

    def test_no_provider_call_in_source(self):
        self.assertNotIn(".complete(", MODULE_SRC)
        self.assertNotIn(".chat(", MODULE_SRC)


class TestForbiddenReferencesAbsent(unittest.TestCase):
    """Guard 3 - forbidden references / non-stdlib imports are absent."""

    def test_forbidden_substrings_absent(self):
        present = [s for s in FORBIDDEN_SUBSTRINGS if s in MODULE_SRC]
        self.assertEqual(present, [], "forbidden substrings present: %s" % present)

    def test_only_stdlib_imports(self):
        tree = ast.parse(MODULE_SRC)
        roots = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    roots.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.level and node.level > 0:
                    self.fail("relative import found; module must be stdlib-only")
                if node.module:
                    roots.add(node.module.split(".")[0])
        offending = roots - ALLOWED_IMPORT_ROOTS
        self.assertEqual(offending, set(), "non-stdlib imports: %s" % offending)


class TestNoLiveWiring(unittest.TestCase):
    """Guard 4 / 6 - no live surface imports or references the new module."""

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
    """Guard 5 - the Spine characterization lock is present.

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
