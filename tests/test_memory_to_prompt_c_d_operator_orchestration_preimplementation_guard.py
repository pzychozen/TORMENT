"""tests/test_memory_to_prompt_c_d_operator_orchestration_preimplementation_guard.py

Tests-only / source-AST PRE-IMPLEMENTATION GUARD for the C-D operator-orchestration
direction (memory-to-prompt / live-caller lane).

The bounded C-D proposal recommends tests-first / characterization-first: land the guardrails
BEFORE any surface code, so the boundaries exist before the thing they guard. This file locks
that the C-D operator-orchestration surface does NOT exist yet and that every production
closure the proposal depends on still holds. It reads source with pathlib + ast.parse only --
it does NOT import or execute production runtime.

The candidate implementation NAMES below are absent / forbidden sentinels: they must appear in
NO .py file except THIS guard, which excludes itself when scanning.

Anchors (docs, not imported):
  - docs/TORMENT_MEMORY_TO_PROMPT_LIVE_CALLER_SOURCE_REVIEW_AFTER_NON_SPINE_PROVIDER_HANDOFF_v0.1.md
  - docs/TORMENT_MEMORY_TO_PROMPT_LIVE_CALLER_ARCHITECTURE_DECISION_FRAME_v0.1.md
  - docs/TORMENT_MEMORY_TO_PROMPT_LIVE_CALLER_C_D_OPERATOR_ORCHESTRATION_EVALUATION_v0.1.md
  - docs/TORMENT_MEMORY_TO_PROMPT_LIVE_CALLER_C_D_BOUNDED_IMPLEMENTATION_PROPOSAL_v0.1.md

This guard authorizes nothing: it does not create, import, or wire any C-D surface.
"""
from __future__ import annotations

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
THIS_FILE = Path(__file__).resolve()

# --- Candidate (absent / forbidden) sentinels -------------------------------- #
CANDIDATE_MODULE_REL = "torment_service/memory_to_prompt_operator_orchestrator.py"
CANDIDATE_HARNESS_REL = "tests/manual/memory_to_prompt_c_d_operator_orchestration_harness.py"
CANDIDATE_NAMES = (
    "memory_to_prompt_operator_orchestrator",
    "MemoryToPromptOperatorOrchestrator",
    "run_memory_to_prompt_operator_orchestration",
    "TORMENT_MEMORY_TO_PROMPT_OPERATOR_ORCHESTRATION",
    "memory_to_prompt_c_d_operator_orchestration_harness",
)
CANDIDATE_ROUTE_TOKENS = ("operator_orchestration", "c_d_operator")

# --- Production surfaces ------------------------------------------------------ #
NON_SPINE_RUNTIME_REL = "torment_service/non_spine_llm_runtime.py"
GATE_ENV = "TORMENT_NON_SPINE_LLM_REAL_PROVIDER"
REAL_ADAPTER = "AnthropicNonSpineLLMProviderAdapter"

# Production surfaces that must stay clear of the non-Spine runtime (invariant 6).
NON_SPINE_FORBIDDEN_FILES = (
    "torment_service/app.py",
    "torment_service/mcp_server.py",
    "torment_service/character.py",
    "torment_service/spine.py",
)
NON_SPINE_FORBIDDEN_DIRS = ("cognition", "roles")

# Real-provider-capable manual surfaces that must stay pytest-refusing (invariant 12).
PYTEST_REFUSING_MANUAL = (
    "tests/manual/non_spine_llm_anthropic_provider_harness.py",
    "tests/manual/non_spine_llm_character_operator_harness.py",
)

_MODEL_IDENTS = frozenset({
    "llm_client", "LLMClient", "openai", "OpenAI", "AsyncOpenAI",
    "anthropic", "Anthropic", "AsyncAnthropic", "ChatCompletion",
})
_MODEL_CALL_ATTRS = frozenset({"complete", "chat", "create_chat_completion", "create_completion"})
_TERRAIN_B = ("AgentRunner", "run_turn", "memory_context_orchestrator",
              "run_turn_with_memory_context")


# --------------------------------------------------------------------------- #
# Source / AST helpers
# --------------------------------------------------------------------------- #

def _read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def _parse(rel):
    return ast.parse(_read(rel))


def _idents(tree):
    out = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Name):
            out.add(n.id)
        elif isinstance(n, ast.Attribute):
            out.add(n.attr)
    return out


def _import_names(tree):
    out = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                out.add(a.name.split(".")[0])
                out.add(a.name.split(".")[-1])
        elif isinstance(n, ast.ImportFrom) and n.module:
            out.add(n.module.split(".")[0])
            out.add(n.module.split(".")[-1])
            for a in n.names:
                out.add(a.name)
    return out


def _func(tree, name):
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name:
            return n
    return None


def _model_boundary_hits(tree):
    """Model-boundary tokens in CODE only (Name/Attribute/import idents + model-call attrs).
    Docstrings/comments are not Name/Attribute nodes, so provider mentions in prose do not
    trip this."""
    hits = set()
    ids = _idents(tree) | _import_names(tree)
    hits |= (ids & _MODEL_IDENTS)
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
                and n.func.attr in _MODEL_CALL_ATTRS:
            hits.add("call:" + n.func.attr)
    return sorted(hits)


def _iter_py(*reldirs):
    for reldir in reldirs:
        base = ROOT / reldir
        if not base.exists():
            continue
        for p in sorted(base.rglob("*.py")):
            parts = p.parts
            if "__pycache__" in parts or any(s.startswith("do_not_touch") for s in parts):
                continue
            yield p.relative_to(ROOT).as_posix()


def _iter_production_py():
    yield from _iter_py("torment_service", "cognition", "roles")


def _iter_repo_py():
    for p in sorted(ROOT.rglob("*.py")):
        parts = p.parts
        if "__pycache__" in parts or any(s.startswith("do_not_touch") for s in parts):
            continue
        yield p


# --------------------------------------------------------------------------- #
# 1-2. Candidate surfaces do not exist yet
# --------------------------------------------------------------------------- #

class TestCandidateSurfacesAbsent(unittest.TestCase):
    def test_no_c_d_orchestration_module_exists(self):  # Invariant 1
        self.assertFalse((ROOT / CANDIDATE_MODULE_REL).exists(),
                         f"C-D orchestration module must not exist yet: {CANDIDATE_MODULE_REL}")

    def test_no_candidate_manual_harness_exists(self):  # Invariant 2
        self.assertFalse((ROOT / CANDIDATE_HARNESS_REL).exists(),
                         f"C-D candidate manual harness must not exist yet: {CANDIDATE_HARNESS_REL}")


# --------------------------------------------------------------------------- #
# 3-5. No production reference / endpoint / tool surface
# --------------------------------------------------------------------------- #

class TestNoProductionSurface(unittest.TestCase):
    def test_no_production_module_references_candidate_names(self):  # Invariant 3
        offenders = {}
        for rel in _iter_production_py():
            present = [n for n in CANDIDATE_NAMES if n in _read(rel)]
            if present:
                offenders[rel] = present
        self.assertEqual(offenders, {},
                         f"production modules must reference no C-D candidate name: {offenders}")

    def test_app_exposes_no_c_d_route_or_schema(self):  # Invariant 4
        src = _read("torment_service/app.py")
        for name in CANDIDATE_NAMES:
            self.assertNotIn(name, src, f"app.py must expose no C-D candidate ({name})")
        for tok in CANDIDATE_ROUTE_TOKENS:
            self.assertNotIn(tok, src, f"app.py must contain no C-D route/schema token ({tok})")

    def test_mcp_server_exposes_no_c_d_tool_or_resource(self):  # Invariant 5
        src = _read("torment_service/mcp_server.py")
        for name in CANDIDATE_NAMES:
            self.assertNotIn(name, src, f"mcp_server.py must expose no C-D candidate ({name})")
        for tok in CANDIDATE_ROUTE_TOKENS:
            self.assertNotIn(tok, src, f"mcp_server.py must contain no C-D tool/resource token ({tok})")


# --------------------------------------------------------------------------- #
# 6-7. Production paths stay closed (non-Spine + AgentRunner)
# --------------------------------------------------------------------------- #

class TestProductionStaysClosed(unittest.TestCase):
    def test_production_does_not_import_non_spine_runtime(self):  # Invariant 6
        targets = list(NON_SPINE_FORBIDDEN_FILES) + list(_iter_py(*NON_SPINE_FORBIDDEN_DIRS))
        offenders = []
        for rel in targets:
            if "non_spine_llm_runtime" in _import_names(_parse(rel)) \
                    or "non_spine_llm_runtime" in _read(rel):
                offenders.append(rel)
        self.assertEqual(offenders, [],
                         f"these surfaces must not import/reference non_spine_llm_runtime: {offenders}")

    def test_no_live_app_server_mcp_caller_of_agentrunner_run_turn(self):  # Invariant 7
        for rel in ("torment_service/app.py", "torment_service/mcp_server.py",
                    "torment_service/spine.py"):
            ids = _idents(_parse(rel)) | _import_names(_parse(rel))
            self.assertNotIn("AgentRunner", ids, f"{rel} must not reference AgentRunner")
            self.assertNotIn("run_turn", ids, f"{rel} must not call run_turn")


# --------------------------------------------------------------------------- #
# 8. /retrieve + assembler remain read-only context-source
# --------------------------------------------------------------------------- #

class TestRetrievalStaysContextSource(unittest.TestCase):
    def test_retrieve_and_assembler_are_context_source_not_generation(self):  # Invariant 8
        ra = _parse("torment_service/retrieval_assembler.py")
        ra_src = _read("torment_service/retrieval_assembler.py")
        for tok in ("assemble_context", "AssembledContext"):
            self.assertIn(tok, ra_src, f"retrieval_assembler must define {tok} (context source)")
        self.assertEqual(_model_boundary_hits(ra), [],
                         "retrieval_assembler must call no model API")
        ra_ids = _idents(ra) | _import_names(ra)
        for forbidden in _TERRAIN_B + ("non_spine_llm_runtime",):
            self.assertNotIn(forbidden, ra_ids,
                             f"retrieval_assembler must not reference {forbidden}")
        # The /retrieve handler stays retrieval/assembly, not a generation caller.
        handler = _func(_parse("torment_service/app.py"), "retrieve_assembled")
        self.assertIsNotNone(handler, "app.py retrieve_assembled handler must exist")
        h_ids = _idents(handler)
        for forbidden in _TERRAIN_B + ("non_spine_llm_runtime", "complete"):
            self.assertNotIn(forbidden, h_ids,
                             f"retrieve_assembled must not reference {forbidden}")


# --------------------------------------------------------------------------- #
# 9-11. No transcript writer / no memory feedback / no auto provider call
# --------------------------------------------------------------------------- #

class TestNoWriteFeedbackOrAutoProvider(unittest.TestCase):
    def test_no_c_d_transcript_or_output_writer_exists(self):  # Invariant 9
        # The C-D surface does not exist, so no C-D-specific transcript/log/output writer can.
        self.assertFalse((ROOT / CANDIDATE_MODULE_REL).exists(),
                         "no C-D module => no C-D output/transcript writer")
        for rel in _iter_production_py():
            self.assertFalse(any(n in _read(rel) for n in CANDIDATE_NAMES),
                             f"{rel} must reference no C-D candidate (no C-D writer path)")

    def test_no_model_output_to_memory_feedback_path(self):  # Invariant 10
        # No production module imports the non-Spine runtime, so non-Spine model output
        # cannot re-enter ingest / retrieval / memory writers.
        importers = [rel for rel in _iter_production_py()
                     if rel != NON_SPINE_RUNTIME_REL and "non_spine_llm_runtime" in _read(rel)]
        self.assertEqual(importers, [],
                         f"no production module may route non-Spine output back to memory: {importers}")

    def test_no_automatic_provider_call_path(self):  # Invariant 11
        # The gated real adapter + gate env appear in production ONLY in the runtime module;
        # nothing else constructs the adapter or sets the gate -> no automatic provider call.
        for rel in _iter_production_py():
            if rel == NON_SPINE_RUNTIME_REL:
                continue
            src = _read(rel)
            self.assertNotIn(REAL_ADAPTER, src,
                             f"{rel} must not construct the real provider adapter")
            self.assertNotIn(GATE_ENV, src,
                             f"{rel} must not set/read the real-provider gate")
        self.assertIn(GATE_ENV, _read(NON_SPINE_RUNTIME_REL),
                      "the non-Spine runtime must keep the explicit real-provider gate")


# --------------------------------------------------------------------------- #
# 12-13. Manual surfaces refuse pytest; sentinels appear only here
# --------------------------------------------------------------------------- #

class TestManualRefusalAndSentinelContainment(unittest.TestCase):
    def test_real_provider_manual_surfaces_remain_pytest_refusing(self):  # Invariant 12
        for rel in PYTEST_REFUSING_MANUAL:
            self.assertIn('"pytest" in sys.modules', _read(rel),
                          f"{rel} must remain pytest-refusing")

    def test_candidate_names_appear_only_in_this_guard(self):  # Invariant 13
        offenders = {}
        for p in _iter_repo_py():
            if p.resolve() == THIS_FILE:
                continue
            src = p.read_text(encoding="utf-8")
            present = [n for n in CANDIDATE_NAMES if n in src]
            if present:
                offenders[p.relative_to(ROOT).as_posix()] = present
        self.assertEqual(offenders, {},
                         f"C-D candidate names must appear only in this guard test: {offenders}")


if __name__ == "__main__":
    unittest.main()
