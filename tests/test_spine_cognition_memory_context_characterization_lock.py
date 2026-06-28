"""tests/test_spine_cognition_memory_context_characterization_lock.py

Tests-only / source-AST characterization LOCK for the live deterministic Spine /
cognition.pipeline memory_context flow and the negative model-boundary facts.

These tests read source files with pathlib + ast.parse only. They do NOT import or execute
production runtime, and they assert structure (AST) for positive call shapes and
negative-existence (source/AST) for absence claims. They are robust to formatting and avoid
brittle line numbers.

Locked facts (see docs/...DETERMINISTIC_MEMORY_CONTEXT_CHARACTERIZATION_FRAME_v0.1.md):
  - live flow: Spine -> run_cognition_pipeline -> route -> build_memory_context ->
    deterministic roles -> reintegrate -> result dict;
  - memory_context is structured retrieval + character + drift, consumed by deterministic roles;
  - no LLM/model/prompt boundary exists in cognition/ or roles/;
  - final_answer is a deterministic concatenation (LLM synthesis is a FUTURE docstring note);
  - /retrieve + AssembledContext.assembled_text are NOT the live Spine path;
  - AgentRunner / Terrain B / memory_context_orchestrator are excluded from the live path;
  - no output-control surfaces and no writeback on the Spine path.

Note: `lane_provider` / `LaneQueryProvider` are RETRIEVAL provider terms in cognition and are
NOT treated as model providers.
"""
from __future__ import annotations

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Unambiguous model-client identifiers (NOT lane_provider / LaneQueryProvider).
_MODEL_IDENTS = frozenset({
    "llm_client", "LLMClient", "openai", "OpenAI", "AsyncOpenAI",
    "anthropic", "Anthropic", "AsyncAnthropic", "system_prompt", "ChatCompletion",
})
# Model-completion call attributes.
_MODEL_CALL_ATTRS = frozenset({"complete", "chat", "create_chat_completion", "create_completion"})


# --------------------------------------------------------------------------- #
# Source/AST helpers
# --------------------------------------------------------------------------- #

def _read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def _parse(rel):
    return ast.parse(_read(rel))


def _func(tree, name):
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name:
            return n
    return None


def _callee_name(call):
    f = call.func
    if isinstance(f, ast.Attribute):
        return f.attr
    if isinstance(f, ast.Name):
        return f.id
    return None


def _call_names(node):
    return [_callee_name(n) for n in ast.walk(node) if isinstance(n, ast.Call)]


def _find_calls(node, name):
    return [n for n in ast.walk(node)
            if isinstance(n, ast.Call) and _callee_name(n) == name]


def _first_lineno(node, name):
    ls = [n.lineno for n in ast.walk(node)
          if isinstance(n, ast.Call) and _callee_name(n) == name and hasattr(n, "lineno")]
    return min(ls) if ls else None


def _call_arg_idents(call):
    out = set()
    for a in list(call.args) + [k.value for k in call.keywords]:
        for x in ast.walk(a):
            if isinstance(x, ast.Name):
                out.add(x.id)
    return out


def _idents(node):
    out = set()
    for n in ast.walk(node):
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
        elif isinstance(n, ast.ImportFrom) and n.module:
            out.add(n.module.split(".")[0])
            for a in n.names:
                out.add(a.name)
    return out


def _model_boundary_hits(tree):
    """Return model-boundary tokens found in CODE (Name/Attribute/import names + model-
    completion call attrs). Docstrings/comments are not Name/Attribute nodes, so the
    'Future versions may use LLM synthesis' note never trips this."""
    hits = set()
    ids = _idents(tree) | _import_names(tree)
    hits |= (ids & _MODEL_IDENTS)
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and _callee_name(n) in _MODEL_CALL_ATTRS:
            hits.add("call:" + _callee_name(n))
    return sorted(hits)


def _iter_py(reldir):
    base = ROOT / reldir
    for p in sorted(base.rglob("*.py")):
        if "__pycache__" in p.parts:
            continue
        yield p.relative_to(ROOT).as_posix()


class TestSpineCognitionMemoryContextCharacterizationLock(unittest.TestCase):

    # 1. Live flow shape in cognition/pipeline.py
    def test_pipeline_flow_routes_builds_memory_context_runs_roles_and_reintegrates(self):
        fn = _func(_parse("cognition/pipeline.py"), "run_cognition_pipeline")
        self.assertIsNotNone(fn, "run_cognition_pipeline not found")
        names = _call_names(fn)
        for need in ("route", "build_memory_context", "reintegrate"):
            self.assertIn(need, names, f"run_cognition_pipeline must call {need}")
        # memory_context assigned from build_memory_context
        assigned = any(
            isinstance(n, ast.Assign) and isinstance(n.value, ast.Call)
            and _callee_name(n.value) == "build_memory_context"
            and any(isinstance(t, ast.Name) and t.id == "memory_context" for t in n.targets)
            for n in ast.walk(fn))
        self.assertTrue(assigned, "memory_context must be assigned from build_memory_context")
        # role.run(... memory_context ...)
        run_calls = _find_calls(fn, "run")
        self.assertTrue(any("memory_context" in _call_arg_idents(c) for c in run_calls),
                        "role.run(...) must receive memory_context")
        # reintegrate(... memory_context ...)
        reint = _find_calls(fn, "reintegrate")
        self.assertTrue(reint and any("memory_context" in _call_arg_idents(c) for c in reint),
                        "reintegrate(...) must receive memory_context")
        # ordering: route -> build_memory_context -> run -> reintegrate
        order = [_first_lineno(fn, nm) for nm in ("route", "build_memory_context", "run", "reintegrate")]
        self.assertTrue(all(x is not None for x in order), f"missing flow call: {order}")
        self.assertEqual(order, sorted(order), f"flow must be ordered route->build->run->reintegrate: {order}")

    # 2. memory_context builder in cognition/apertures.py
    def test_memory_context_shape_is_structured_retrieval_character_drift(self):
        ap = _parse("cognition/apertures.py")
        fn = _func(ap, "build_memory_context")
        self.assertIsNotNone(fn, "build_memory_context not found")
        ids = _idents(fn)
        for field in ("private_memories", "shared_memories", "deep_memories",
                      "character_context", "drift_snapshot"):
            self.assertIn(field, ids, f"build_memory_context must use {field}")
        self.assertIn("MemoryContext", _idents(ap), "apertures must reference MemoryContext")

    # 3. Deterministic role package
    def test_roles_have_no_model_prompt_boundary(self):
        scanned = 0
        for rel in _iter_py("roles"):
            scanned += 1
            hits = _model_boundary_hits(_parse(rel))
            self.assertEqual(hits, [], f"{rel} has model-boundary tokens: {hits}")
        self.assertGreater(scanned, 0, "expected to scan the roles package")

    # 4. Deterministic cognition package
    def test_cognition_has_no_model_prompt_boundary(self):
        scanned = 0
        for rel in _iter_py("cognition"):
            scanned += 1
            hits = _model_boundary_hits(_parse(rel))
            self.assertEqual(hits, [], f"{rel} has model-boundary tokens: {hits}")
        self.assertGreater(scanned, 0, "expected to scan the cognition package")

    # 5. final_answer deterministic in cognition/reintegration.py
    def test_reintegration_final_answer_is_deterministic_not_model_synthesized(self):
        rt = _parse("cognition/reintegration.py")
        bfa = _func(rt, "_build_final_answer")
        self.assertIsNotNone(bfa, "_build_final_answer not found")
        reint = _func(rt, "reintegrate")
        self.assertIsNotNone(reint)
        self.assertIn("_build_final_answer", _call_names(reint),
                      "reintegrate must call _build_final_answer")
        # deterministic concatenation evidence: a .join(...) call
        self.assertTrue(_find_calls(bfa, "join"),
                        "_build_final_answer must use a deterministic join/concatenation")
        # no model boundary in the whole reintegration module
        self.assertEqual(_model_boundary_hits(rt), [], "reintegration must call no model API")

    # 6. Spine live path in torment_service/spine.py
    def test_spine_full_cognition_calls_pipeline_not_agentrunner_or_orchestrator(self):
        sp = _parse("torment_service/spine.py")
        fc = _func(sp, "_full_cognition")
        self.assertIsNotNone(fc, "_full_cognition not found")
        self.assertIn("run_cognition_pipeline", _call_names(fc),
                      "_full_cognition must call run_cognition_pipeline")
        ids = _idents(fc)
        for forbidden in ("AgentRunner", "run_turn", "memory_context_orchestrator",
                          "run_turn_with_memory_context"):
            self.assertNotIn(forbidden, ids, f"_full_cognition must not reference {forbidden}")
        # no ingest_fn / lookup_fn passed into the pipeline (writeback structurally disabled)
        rcp = _find_calls(fc, "run_cognition_pipeline")[0]
        kw = {k.arg for k in rcp.keywords}
        self.assertNotIn("ingest_fn", kw, "Spine path must pass no ingest_fn")
        self.assertNotIn("lookup_fn", kw, "Spine path must pass no lookup_fn")
        # query_fn defined and fabric.query used as retrieval source
        self.assertIn("query_fn", ids, "_full_cognition must define/pass query_fn")
        self.assertIn("query", ids, "_full_cognition must source retrieval via fabric.query")
        # _fast_query_memory (if present) is retrieval-only: no model/AgentRunner/orchestrator
        fqm = _func(sp, "_fast_query_memory")
        if fqm is not None:
            fids = _idents(fqm)
            for forbidden in ("AgentRunner", "run_turn", "memory_context_orchestrator",
                              "run_turn_with_memory_context"):
                self.assertNotIn(forbidden, fids,
                                 f"_fast_query_memory must not reference {forbidden}")
            self.assertEqual(_model_boundary_hits(ast.Module(body=[fqm], type_ignores=[])), [],
                             "_fast_query_memory must call no model API")

    # 7. app.py endpoint surface stays Spine/retrieve, not AgentRunner
    def test_app_endpoints_stay_spine_or_retrieve_not_agentrunner(self):
        app = _parse("torment_service/app.py")
        app_src = _read("torment_service/app.py")
        for route in ("/agent/query", "/cognition/run", "/spine/submit_task", "/retrieve"):
            self.assertIn(route, app_src, f"endpoint {route} must exist")
        for handler in ("query", "cognition_run", "spine_submit_task", "retrieve_assembled"):
            self.assertIsNotNone(_func(app, handler), f"handler {handler} must exist")
        ids = _idents(app) | _import_names(app)
        # Spine / retrieval terrain present:
        self.assertIn("submit_task", ids, "app must route through submit_task (Spine terrain)")
        self.assertIn("run_cognition_pipeline", ids, "app must use run_cognition_pipeline")
        # AgentRunner / orchestrator terrain absent:
        for forbidden in ("AgentRunner", "run_turn", "memory_context_orchestrator",
                          "run_turn_with_memory_context"):
            self.assertNotIn(forbidden, ids, f"app must not reference {forbidden}")

    # 8. /retrieve / AssembledContext outside the live Spine path
    def test_retrieve_assembled_context_is_not_live_spine_path(self):
        ra = _read("torment_service/retrieval_assembler.py")
        for tok in ("assemble_context", "AssembledContext", "assembled_text"):
            self.assertIn(tok, ra, f"retrieval_assembler must define {tok}")
        pipe_ids = _idents(_parse("cognition/pipeline.py")) | _import_names(_parse("cognition/pipeline.py"))
        spine_ids = _idents(_parse("torment_service/spine.py")) | _import_names(_parse("torment_service/spine.py"))
        for tok in ("assemble_context", "AssembledContext", "assembled_text", "retrieval_assembler"):
            self.assertNotIn(tok, pipe_ids, f"cognition.pipeline must not reference {tok}")
            self.assertNotIn(tok, spine_ids, f"spine must not reference {tok}")

    # 9. AgentRunner / Terrain B excluded from the live path
    def test_agentrunner_and_terrain_b_remain_excluded_from_live_path(self):
        terrain_b = ("AgentRunner", "run_turn", "memory_context_orchestrator",
                     "run_turn_with_memory_context")
        for reldir in ("cognition", "roles"):
            for rel in _iter_py(reldir):
                ids = _idents(_parse(rel)) | _import_names(_parse(rel))
                for forbidden in terrain_b:
                    self.assertNotIn(forbidden, ids, f"{rel} must not reference {forbidden}")
        sp = _parse("torment_service/spine.py")
        sp_ids = _idents(sp) | _import_names(sp)
        for forbidden in terrain_b:
            self.assertNotIn(forbidden, sp_ids, f"spine must not reference {forbidden}")
        # memory_context_orchestrator not imported by spine/app/cognition/roles; agent_loop excluded
        for rel in (["torment_service/spine.py", "torment_service/app.py"]
                    + list(_iter_py("cognition")) + list(_iter_py("roles"))):
            imports = _import_names(_parse(rel))
            self.assertNotIn("memory_context_orchestrator", imports,
                             f"{rel} must not import memory_context_orchestrator")
            self.assertNotIn("agent_loop", imports, f"{rel} must not import agent_loop")

    # 10. No output-control surfaces on the live path
    def test_no_output_control_surfaces_on_live_path(self):
        # Specific compound output-steering identifiers (governance/drift identity gates and
        # ordinary words like "review" are NOT model-output steering and are allowed).
        forbidden = ("rerank", "rerank_output", "style_steer", "style_control",
                     "suppress_output", "output_suppression", "response_rewrite",
                     "rewrite_response", "output_finalizer", "retry_generation")
        targets = ["torment_service/spine.py"] + list(_iter_py("cognition")) + list(_iter_py("roles"))
        for rel in targets:
            ids = _idents(_parse(rel))
            for tok in forbidden:
                self.assertNotIn(tok, ids, f"{rel} must not contain output-control ident {tok}")

    # 11. No write/persistence/transcript writeback on the Spine path
    def test_no_writeback_or_transcript_on_spine_path(self):
        sp = _parse("torment_service/spine.py")
        fc = _func(sp, "_full_cognition")
        self.assertIsNotNone(fc)
        rcp = _find_calls(fc, "run_cognition_pipeline")[0]
        kw = {k.arg for k in rcp.keywords}
        self.assertFalse({"ingest_fn", "lookup_fn"} & kw,
                         "_full_cognition must enable no writeback (no ingest_fn/lookup_fn)")
        ids = _idents(fc)
        for tok in ("ingest_fn", "lookup_fn", "writeback", "save_transcript", "write_log"):
            self.assertNotIn(tok, ids, f"_full_cognition must not reference {tok}")
        # no file open() inside _full_cognition
        opens = [n for n in ast.walk(fc)
                 if isinstance(n, ast.Call) and _callee_name(n) == "open"]
        self.assertEqual(opens, [], "_full_cognition must open no files")


if __name__ == "__main__":
    unittest.main()
