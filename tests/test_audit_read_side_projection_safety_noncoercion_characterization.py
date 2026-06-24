"""Tests-only / source-only characterization: read-side projection safety and
non-coercion (P4 O3/O4, substrate-independent subset).

Complements the sealed audit observe-authority lane and the MemoryPlan shaping
non-control lock by covering the remaining edge: how retrieved / projected memory
shapes prompt context without becoming authority. Grounded in the ratified P4
Reader/Projection-Safety Contract (O3 intent + re-entry classification; O4
explicit projection gating) and the Guidance-Without-Coercion retrieval-influence
surface map.

Doctrine:
    Memory may shape context. Memory may not seize authority.
    Audit observes authority. Audit must not become authority.

Properties locked (substrate-independent):
  * O3 — read/debug/trace surfaces are classified by what they actually do
    (read-only, no generation/writer), not by a "debug"/"trace"/"audit" label.
  * O4 — caller-visible projection is explicit and surface-local; caller-visible
    does not automatically mean prompt-visible.
  * /agent/query, /retrieve, /thinking/debug, the deep-memory query, and trace
    surfaces remain classified read/projection surfaces, not generation owners.
  * spirit-return, warmth, SRG, voice-cue, flavor, and drift are bounded
    guidance/context signals, not eligibility authority.
  * warmth recursion is post-selection (depends only on retrieval history) and
    cannot change semantic candidate eligibility.
  * spirit-return echo is positive-only / absence-neutral (mismatch -> 0.0,
    never a penalty).
  * SRG influence stays gated (default-off) and bounded where present.
  * voice-cue / flavor / drift may shape assembled (model-visible) context where
    already live, but make no review/output/writer/generation calls.

Wording corrections honored: this does NOT claim all identity/substrate-ish
fields are absent from caller-visible surfaces, and does NOT claim guidance
signals cannot shape model-visible context. The lock is classified projection,
bounded guidance, no silent authority expansion, and no write/control feedback.

Deferred / out of scope (NOT asserted satisfied here): P4 O1/O2 source-sameness /
source-membership, carrier mechanics, database/substrate, Gate D, Envelope Audit
runtime, private-owner live wiring, Shape B, writer path, retrieval feedback,
persistence changes, autonomy, public API/schema, prompt-request exposure,
AgentRunner ownership, MCP/action-surface changes.
"""

import ast
import inspect
import os
import re
import unittest

from torment_service.spirit_return import (
    compute_symbol_interaction,
    compute_warmth,
    SYMBOL_MEANINGS,
    WARMTH_FLOOR,
    WARMTH_CAP,
)


# --------------------------------------------------------------------------- #
# Source / AST helpers
# --------------------------------------------------------------------------- #

def _repo_root():
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(here)


def _service_dir():
    return os.path.join(_repo_root(), "torment_service")


def _docs_dir():
    return os.path.join(_repo_root(), "docs")


def _src(filename, base=None):
    base = base or _service_dir()
    with open(os.path.join(base, filename), "r", encoding="utf-8") as fh:
        return fh.read()


def _tree(filename):
    with open(os.path.join(_service_dir(), filename), "rb") as fh:
        return ast.parse(fh.read().replace(b"\x00", b""))


def _top_func(tree, name):
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name:
            return n
    return None


def _idents(node):
    out = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Name):
            out.add(n.id)
        elif isinstance(n, ast.Attribute):
            out.add(n.attr)
    return out


def _called_names(node):
    out = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Call):
            f = n.func
            if isinstance(f, ast.Name):
                out.add(f.id)
            elif isinstance(f, ast.Attribute):
                out.add(f.attr)
    return out


def _import_leaves(tree):
    leaves = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for x in n.names:
                leaves.add(x.name.split(".")[-1])
        elif isinstance(n, ast.ImportFrom):
            if n.module:
                leaves.add(n.module.split(".")[-1])
    return leaves


def _env_get_default(tree, var_name):
    for n in ast.walk(tree):
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr == "get" and len(n.args) >= 2
                and isinstance(n.args[0], ast.Constant) and n.args[0].value == var_name
                and isinstance(n.args[1], ast.Constant)):
            return n.args[1].value
    return None


# Generation / writer ownership a read/projection surface must NOT take on.
_GENERATION_OWNER_CALLS = {"run_turn", "complete"}
_WRITER_CALLS = {"ingest", "promote_chunk", "promote_chunk_endpoint", "spawn_memory",
                 "add_memory", "reinforce", "save_state", "append_record",
                 "gravity_correction"}


# --------------------------------------------------------------------------- #
# Spirit-return: positive-only echo + bounded, history-only warmth (behavioral)
# --------------------------------------------------------------------------- #

class TestSpiritReturnGuidanceBoundedAndPositive(unittest.TestCase):

    def _symbols(self):
        syms = list(SYMBOL_MEANINGS.keys())
        # Include the default glyph used when metadata is missing.
        if "◯" not in syms:           # ◯
            syms.append("◯")
        return syms or ["◯", "A", "B"]

    def test_symbol_interaction_confidence_boost_never_negative(self):
        # Positive-only / absence-neutral: no symbol pairing yields a penalty.
        syms = self._symbols()
        for birth in syms:
            for current in syms:
                r = compute_symbol_interaction(birth, current)
                self.assertGreaterEqual(
                    r["confidence_boost"], 0.0,
                    msg=f"negative boost for ({birth!r},{current!r}): {r}")

    def test_same_symbol_echo_is_positive_and_a_resonance_candidate(self):
        sym = self._symbols()[0]
        r = compute_symbol_interaction(sym, sym)
        self.assertGreater(r["confidence_boost"], 0.0)
        self.assertTrue(r["is_resonance_candidate"])

    def test_absence_neutral_pairing_exists(self):
        # At least one pairing is absence-neutral (boost 0.0, not a candidate) —
        # mismatch costs nothing rather than penalizing.
        syms = self._symbols()
        neutral = [
            compute_symbol_interaction(b, c)
            for b in syms for c in syms
            if compute_symbol_interaction(b, c)["confidence_boost"] == 0.0
        ]
        self.assertTrue(neutral, "expected at least one absence-neutral pairing")
        for r in neutral:
            self.assertFalse(r["is_resonance_candidate"])

    def test_warmth_is_bounded(self):
        grid = [(0, 0), (1, 0), (2, 0), (3, 10), (5, 50), (100, 0), (50, 99999)]
        for ac, steps in grid:
            w = compute_warmth(ac, steps)
            self.assertGreaterEqual(w, WARMTH_FLOOR)
            self.assertLessEqual(w, WARMTH_CAP)
        self.assertEqual(compute_warmth(0, 0), WARMTH_FLOOR)
        self.assertEqual(compute_warmth(100, 0), WARMTH_CAP)            # cap holds
        self.assertEqual(compute_warmth(50, 99999), WARMTH_FLOOR)       # window reset

    def test_warmth_depends_only_on_retrieval_history(self):
        # Post-selection: warmth is a function of appearance history only — it
        # takes no query / candidate / semantic-content input, so it structurally
        # cannot change semantic candidate eligibility.
        params = list(inspect.signature(compute_warmth).parameters)
        self.assertEqual(params, ["appearance_count", "steps_since_first"])


# --------------------------------------------------------------------------- #
# Assembler: warmth is secondary ordering; voice/flavor/drift are text-only
# --------------------------------------------------------------------------- #

class TestAssemblerOrderingAndTextProjection(unittest.TestCase):

    def setUp(self):
        self.src = _src("retrieval_assembler.py")
        self.tree = _tree("retrieval_assembler.py")

    def test_warmth_is_secondary_sort_key_after_score(self):
        # score is the primary sort key; warmth_score is only the secondary key.
        self.assertIn('(b.score, b.metadata.get("warmth_score"', self.src)

    def test_inclusion_is_token_budget_gated_not_warmth_alone(self):
        # Classification != inclusion: per-block token budget still governs which
        # classified blocks actually make it into the assembled context.
        self.assertIn("budget_per_block", self.src)

    def test_spirit_resonance_classifies_to_identity_block(self):
        self.assertIn("from_spirit_return", self.src)
        self.assertIn("BLOCK_IDENTITY", self.src)

    def test_voice_flavor_drift_are_model_visible_text_projection(self):
        # These DO shape model-visible context (allowed) — recorded, not denied.
        self.assertIn("[Voice:", self.src)
        self.assertIn("[Flavor:", self.src)
        self.assertIn("[Drift:", self.src)

    def test_drift_projection_is_conditional(self):
        # Drift text is gated by drift_info presence (conditional projection).
        self.assertIn("[Drift:", self.src)
        self.assertIn("drift_info", self.src)

    def test_assembler_makes_no_generation_or_writer_calls(self):
        called = _called_names(self.tree)
        offenders = called & (_GENERATION_OWNER_CALLS | _WRITER_CALLS)
        self.assertEqual(offenders, set(),
                         msg=f"assembler performs control/writer calls: {sorted(offenders)}")

    def test_assembler_does_not_couple_to_generation_or_endpoint(self):
        leaves = _import_leaves(self.tree)
        self.assertNotIn("agent_loop", leaves)
        self.assertNotIn("app", leaves)


# --------------------------------------------------------------------------- #
# SRG: gated (default-off) and bounded where present
# --------------------------------------------------------------------------- #

class TestSrgGatedAndBounded(unittest.TestCase):

    def setUp(self):
        self.src = _src("fabric.py")
        self.tree = _tree("fabric.py")

    def test_srg_source_default_off(self):
        self.assertEqual(_env_get_default(self.tree, "TORMENT_SRG_ENABLE"), "0")

    def test_srg_multiplier_application_is_gated(self):
        self.assertIn("if self._srg_enable:", self.src)

    def test_score_multipliers_are_bounded_not_authority(self):
        # Literal score multipliers (the SRG nudges) stay modest — bounded above by
        # a small ceiling, never a large authority multiplier. Tuning within the
        # band is NOT frozen (only the bound is locked).
        mults = [float(x) for x in re.findall(r"final \*= (\d+\.\d+)", self.src)]
        self.assertTrue(mults, "expected at least one literal score multiplier")
        for m in mults:
            self.assertGreater(m, 1.0)
            self.assertLessEqual(m, 1.2, msg=f"score multiplier {m} exceeds bound")


# --------------------------------------------------------------------------- #
# O3/O4: read/projection surfaces are not generation owners; explicit projection
# --------------------------------------------------------------------------- #

class TestReadProjectionSurfacesNotGenerationOwners(unittest.TestCase):

    def setUp(self):
        self.app = _tree("app.py")
        self.query = _top_func(self.app, "query")                  # /agent/query
        self.retrieve = _top_func(self.app, "retrieve_assembled")  # /retrieve
        self.debug = _top_func(self.app, "thinking_debug")         # /thinking/debug
        for fn, nm in ((self.query, "query"), (self.retrieve, "retrieve_assembled"),
                       (self.debug, "thinking_debug")):
            self.assertIsNotNone(fn, f"{nm} handler not found")

    def _assert_not_generation_owner(self, fn):
        ids = _idents(fn)
        self.assertNotIn("run_turn", ids)
        self.assertNotIn("AgentRunner", ids)
        self.assertNotIn("complete", ids)

    def test_agent_query_is_retrieval_not_generation(self):
        # O3: classified by behavior — returns fabric.query, not generation.
        self._assert_not_generation_owner(self.query)

    def test_retrieve_is_assembly_not_generation(self):
        self.assertIn("assemble_context", _idents(self.retrieve))
        self._assert_not_generation_owner(self.retrieve)

    def test_thinking_debug_is_readonly_decision_chain(self):
        ids = _idents(self.debug)
        self.assertIn("think", ids)
        self.assertIn("to_dict", ids)
        self._assert_not_generation_owner(self.debug)
        # O3: not a writer either — the "debug" label is not its safety boundary;
        # its read-only nature is structural.
        self.assertEqual(_called_names(self.debug) & _WRITER_CALLS, set())

    def test_caller_visible_memoryplan_projection_is_explicit_and_named(self):
        # O4: /agent/query projects the MemoryPlan as an explicit, named lane dict
        # (surface-local), not a blind default spread. (We do NOT assert that any
        # particular identity/substrate field is absent.)
        app_src = _src("app.py")
        self.assertIn('"top_k_by_lane": _plan.top_k_by_lane', app_src)
        self.assertIn('"weight_by_lane": _plan.weight_by_lane', app_src)

    def test_caller_visible_is_not_automatically_prompt_visible(self):
        # O4: none of these caller-facing surfaces build a model prompt from their
        # output (no generation call), so caller-visible != prompt-visible.
        for fn in (self.query, self.retrieve, self.debug):
            self.assertEqual(_idents(fn) & _GENERATION_OWNER_CALLS, set())


# --------------------------------------------------------------------------- #
# Deferred-scope boundary (docs): O1/O2 + carriers remain out of scope here
# --------------------------------------------------------------------------- #

class TestDeferredScopeBoundary(unittest.TestCase):

    def test_p4_contract_keeps_o1_o2_source_sameness_carrier_dependent(self):
        # This file characterizes only the substrate-independent O3/O4 subset;
        # O1/O2 source-sameness remain carrier-dependent and are NOT asserted
        # satisfied here. Confirm the contract still frames them that way.
        contract = _src(
            "TORMENT_MEMORY_ENGINE_P4_READER_PROJECTION_SAFETY_CONTRACT_v0.1.md",
            base=_docs_dir())
        lc = contract.lower()
        self.assertIn("source-sameness", lc)
        self.assertIn("carrier", lc)
        self.assertIn("o1", lc)
        self.assertIn("o2", lc)

    def test_surface_map_records_positive_only_posture(self):
        # The non-coercion lens this file applies is grounded in the surface map.
        sm = _src("GUIDANCE_WITHOUT_COERCION_RETRIEVAL_INFLUENCE_SURFACE_MAP_v0.1.md",
                  base=_docs_dir())
        self.assertIn("positive-only", sm.lower())


if __name__ == "__main__":
    unittest.main()
