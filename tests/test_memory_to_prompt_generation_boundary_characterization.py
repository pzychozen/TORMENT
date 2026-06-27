"""tests/test_memory_to_prompt_generation_boundary_characterization.py

Tests-only / source-only / AST-only characterization: LOCK THE CURRENT SOURCE TERRAIN
before any future memory-to-prompt-for-generation implementation proposal.

This is NOT implementation, NOT a prompt change, NOT memory injection, NOT
retrieval-to-generation wiring, and NOT endpoint/API/schema work. It parses source
(it never imports `torment_service`, never executes production behavior, and never
calls a model) and asserts the *present* facts the design frame
(`docs/TORMENT_MEMORY_TO_PROMPT_FOR_GENERATION_DESIGN_FRAME_v0.1.md`) named as the
baseline:

  1. AgentRunner generation is MEMORY-BLIND today: `_build_system_prompt(frame, mode)`
     minimal prompt + `frame.raw_input` messages, via `_LLMPromptRequest` →
     `_complete_llm_prompt_request(...)`.
  2. The prompt/generation methods in `agent_loop.py` do not import/call/consume
     assemble_context / AssembledContext / assembled_text / retrieval_assembler /
     character_context / selected audit items / `/retrieve` surfaces.
  3. `/retrieve` (`retrieve_assembled`) / `assemble_context` own assembly terrain but
     call no AgentRunner / run_turn / `_build_llm_prompt_request` /
     `_complete_llm_prompt_request` / model completion.
  4. Public endpoint/API source does not wire retrieved/assembled memory into AgentRunner
     generation.
  5. Current source has NO memory-to-prompt implementation (no model-visible memory
     injection / retrieval-to-generation wiring into the generation boundary).

It asserts NO future memory source, NO injection point, NO prompt format/representation,
reopens NO U1 / audit-owner / dual-ownership question, touches NO `PrivateGenerationOwner`,
and claims NO future proof obligation is satisfied. It only pins what is true now.
"""
from __future__ import annotations

import ast
import os
import unittest
from functools import lru_cache


# --------------------------------------------------------------------------- #
# Source/AST helpers (mirrors tests/test_audit_provenance_caller_inventory.py)
# --------------------------------------------------------------------------- #

# Memory / assembly identifiers the generation boundary must not consume.
_MEMORY_ASSEMBLY_IDENTS = frozenset({
    "assemble_context", "AssembledContext", "assembled_text", "retrieval_assembler",
    "character_context", "selected_admitted_items", "audit_admitted_context_items",
    "retrieve_assembled",
})

# The subset that denotes actual memory CONTENT flowing into a call (distinct from the
# audit-observation seam `audit_admitted_context_items`, which is the existing approved
# bridge, not memory-to-prompt-for-generation).
_MEMORY_CONTENT_IDENTS = frozenset({
    "assemble_context", "AssembledContext", "assembled_text", "character_context",
})

# Model-completion call names (a generation boundary).
_GENERATION_CALLS = frozenset({
    "complete", "completion", "completions", "chat", "chat_completion",
    "create_completion", "create_chat_completion", "generate", "predict", "infer",
})

# Callees that constitute the generation boundary / runner entry.
_GEN_BOUNDARY_CALLEES = frozenset(
    {"run_turn", "_complete_llm_prompt_request", "_build_llm_prompt_request"}
) | _GENERATION_CALLS

_SKIP_DIRS = {".git", "__pycache__", ".mypy_cache", ".pytest_cache", ".venv", "node_modules"}


def _repo_root():
    here = os.path.dirname(os.path.abspath(__file__))   # tests/
    return os.path.dirname(here)                          # torment_fabric/


def _rel(path):
    return os.path.relpath(path, _repo_root()).replace("\\", "/")


def _parse_bytes(raw):
    # Null-strip defends against a mount-corruption artifact in some sandboxes; the
    # authoritative repo parses cleanly either way.
    return ast.parse(raw.replace(b"\x00", b""))


def _service_dir():
    return os.path.join(_repo_root(), "torment_service")


def _parse_service(filename):
    with open(os.path.join(_service_dir(), filename), "rb") as fh:
        return _parse_bytes(fh.read())


def _class(tree, name):
    for n in tree.body:
        if isinstance(n, ast.ClassDef) and n.name == name:
            return n
    return None


def _method(cls, name):
    if cls is None:
        return None
    for n in cls.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name:
            return n
    return None


def _func(tree, name):
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name:
            return n
    return None


def _idents(*nodes):
    out = set()
    for node in nodes:
        if node is None:
            continue
        for n in ast.walk(node):
            if isinstance(n, ast.Name):
                out.add(n.id)
            elif isinstance(n, ast.Attribute):
                out.add(n.attr)
            elif isinstance(n, ast.keyword) and n.arg:
                out.add(n.arg)
    return out


def _import_leaves(tree):
    leaves, names = set(), set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for x in n.names:
                leaves.add(x.name.split(".")[-1])
                names.add(x.name.split(".")[-1])
        elif isinstance(n, ast.ImportFrom):
            if n.module:
                leaves.add(n.module.split(".")[-1])
            for x in n.names:
                names.add(x.name)
    return leaves, names


def _callee_name(call):
    f = call.func
    if isinstance(f, ast.Attribute):
        return f.attr
    if isinstance(f, ast.Name):
        return f.id
    return None


def _calls_callee(node, name):
    return any(isinstance(n, ast.Call) and _callee_name(n) == name for n in ast.walk(node))


def _memory_into_generation_hits(tree):
    """Calls to a generation-boundary callee whose arguments carry memory CONTENT
    identifiers — i.e. retrieval/assembly memory wired into generation."""
    hits = []
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call):
            continue
        if _callee_name(n) not in _GEN_BOUNDARY_CALLEES:
            continue
        arg_idents = set()
        for v in list(n.args) + [k.value for k in n.keywords]:
            for x in ast.walk(v):
                if isinstance(x, ast.Name):
                    arg_idents.add(x.id)
                elif isinstance(x, ast.Attribute):
                    arg_idents.add(x.attr)
        bad = arg_idents & _MEMORY_CONTENT_IDENTS
        if bad:
            hits.append((_callee_name(n), sorted(bad)))
    return hits


@lru_cache(maxsize=1)
def _production_py():
    """Relative paths of production torment_service/*.py (excludes tests)."""
    out = []
    for dirpath, dirnames, filenames in os.walk(_service_dir()):
        dirnames[:] = [d for d in dirnames
                       if d not in _SKIP_DIRS and not d.startswith("do_not_touch")]
        for fn in filenames:
            if fn.endswith(".py"):
                out.append(_rel(os.path.join(dirpath, fn)))
    return out


# --------------------------------------------------------------------------- #
# Sanity — guard against vacuous negatives from a parse/lookup miss
# --------------------------------------------------------------------------- #

class TestSanity(unittest.TestCase):
    def test_agent_loop_generation_methods_present(self):
        cls = _class(_parse_service("agent_loop.py"), "AgentRunner")
        self.assertIsNotNone(cls, "AgentRunner class not found")
        for name in ("_build_system_prompt", "_build_llm_prompt_request",
                     "_execute", "_complete_llm_prompt_request"):
            self.assertIsNotNone(_method(cls, name), f"AgentRunner.{name} not found")
        self.assertIsNotNone(_class(_parse_service("agent_loop.py"), "_LLMPromptRequest"),
                             "_LLMPromptRequest not found")

    def test_app_retrieve_and_query_handlers_present(self):
        app = _parse_service("app.py")
        self.assertIsNotNone(_func(app, "retrieve_assembled"), "retrieve_assembled not found")
        self.assertIsNotNone(_func(app, "query"), "query handler not found")


# --------------------------------------------------------------------------- #
# 1 + 2 — generation is memory-blind; prompt methods consume no assembly/memory
# --------------------------------------------------------------------------- #

class TestGenerationIsMemoryBlind(unittest.TestCase):
    def setUp(self):
        self.cls = _class(_parse_service("agent_loop.py"), "AgentRunner")

    def test_build_system_prompt_consumes_no_memory(self):
        idents = _idents(_method(self.cls, "_build_system_prompt"))
        self.assertEqual(idents & _MEMORY_ASSEMBLY_IDENTS, set(),
                         "the minimal system prompt references memory/assembly terrain")

    def test_build_llm_prompt_request_consumes_no_memory(self):
        idents = _idents(_method(self.cls, "_build_llm_prompt_request"))
        self.assertEqual(idents & _MEMORY_ASSEMBLY_IDENTS, set(),
                         "the prompt-request builder references memory/assembly terrain")

    def test_execute_and_completion_helper_consume_no_memory(self):
        idents = _idents(_method(self.cls, "_execute"),
                         _method(self.cls, "_complete_llm_prompt_request"))
        self.assertEqual(idents & _MEMORY_ASSEMBLY_IDENTS, set(),
                         "the generation path references memory/assembly terrain")

    def test_agent_loop_imports_no_assembler_or_assembled_context(self):
        leaves, names = _import_leaves(_parse_service("agent_loop.py"))
        self.assertNotIn("retrieval_assembler", leaves, "agent_loop imports retrieval_assembler")
        self.assertNotIn("AssembledContext", names, "agent_loop imports AssembledContext")
        self.assertNotIn("assemble_context", names, "agent_loop imports assemble_context")


# --------------------------------------------------------------------------- #
# 3 — /retrieve owns assembly terrain but does not generate / call the runner
# --------------------------------------------------------------------------- #

class TestRetrieveOwnsAssemblyNotGeneration(unittest.TestCase):
    def test_retrieve_assembled_assembles_but_does_not_generate(self):
        fn = _func(_parse_service("app.py"), "retrieve_assembled")
        idents = _idents(fn)
        # Owns assembly terrain.
        self.assertIn("assemble_context", idents, "retrieve_assembled does not assemble")
        # Calls no runner / generation boundary.
        for forbidden in ("AgentRunner", "run_turn", "_build_llm_prompt_request",
                          "_complete_llm_prompt_request"):
            self.assertNotIn(forbidden, idents,
                             f"retrieve_assembled references generation surface {forbidden}")
        self.assertEqual(idents & _GENERATION_CALLS, set(),
                         "retrieve_assembled performs a model-completion call")


# --------------------------------------------------------------------------- #
# 4 — public endpoint/API source does not wire memory into AgentRunner generation
# --------------------------------------------------------------------------- #

class TestEndpointsDoNotWireMemoryToGeneration(unittest.TestCase):
    def test_app_does_not_import_or_call_agent_runner(self):
        app = _parse_service("app.py")
        leaves, names = _import_leaves(app)
        self.assertNotIn("agent_loop", leaves, "app.py imports agent_loop")
        self.assertNotIn("AgentRunner", names, "app.py imports AgentRunner")
        self.assertFalse(_calls_callee(app, "run_turn"), "app.py calls run_turn")

    def test_app_does_not_reference_generation_prompt_internals(self):
        idents = _idents(_parse_service("app.py"))
        for forbidden in ("_LLMPromptRequest", "_build_llm_prompt_request",
                          "_complete_llm_prompt_request", "_build_system_prompt"):
            self.assertNotIn(forbidden, idents,
                             f"app.py references generation-prompt internal {forbidden}")

    def test_app_has_no_memory_into_generation_call(self):
        self.assertEqual(_memory_into_generation_hits(_parse_service("app.py")), [],
                         "app.py wires assembled/retrieved memory into a generation call")


# --------------------------------------------------------------------------- #
# 5 — no memory-to-prompt implementation anywhere in production source
# --------------------------------------------------------------------------- #

class TestNoMemoryToPromptImplementation(unittest.TestCase):
    def test_no_production_module_wires_memory_into_generation(self):
        offenders = {}
        for rel in _production_py():
            with open(os.path.join(_repo_root(), rel), "rb") as fh:
                try:
                    tree = _parse_bytes(fh.read())
                except (SyntaxError, ValueError):
                    continue
            hits = _memory_into_generation_hits(tree)
            if hits:
                offenders[rel] = hits
        self.assertEqual(
            offenders, {},
            msg=("memory CONTENT wired into a generation boundary in production "
                 f"(retrieval-to-generation wiring exists): {offenders}"),
        )

    def test_llm_prompt_request_stays_runner_internal(self):
        # The request type is referenced only inside agent_loop (runner-local); no other
        # production module references it (no prompt exposure / public surface change).
        offenders = []
        for rel in _production_py():
            if rel == "torment_service/agent_loop.py":
                continue
            with open(os.path.join(_repo_root(), rel), "rb") as fh:
                try:
                    tree = _parse_bytes(fh.read())
                except (SyntaxError, ValueError):
                    continue
            if "_LLMPromptRequest" in _idents(tree):
                offenders.append(rel)
        self.assertEqual(offenders, [],
                         msg=f"_LLMPromptRequest referenced outside the runner: {offenders}")


if __name__ == "__main__":
    unittest.main()
