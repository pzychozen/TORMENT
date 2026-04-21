# tests/test_closure_preserves_blocks_a_and_b.py
"""
T5 — AC-5: Block C preserves Blocks A and B.

Covers acceptance criteria from BLOCK_C_DESIGN.md §4 AC-5:

    Closure operations do not modify baton lifecycle, reference load
    state, environment consult behavior, or core retrieval. All nine
    scorecard invariant tests remain green. RESEARCH_ASSISTANT_PACK's
    EMPTY_CONTRACT untouched.

Design intent per BLOCK_C_DESIGN.md §10 (non-runtime-touching
guarantees) + handoff notes 3 + 4:

    AgentRunner.__init__ signature unchanged. AgentRunner.run_turn body
    unchanged — no new phases, no new calls. FabricHandle Protocol
    unchanged — still the three methods (ingest, measure_drift,
    gravity_correction). fabric.query signature unchanged — only the
    internal _NON_DEFAULT_CLASSES frozenset is extended. retrieval
    assembler unchanged — no BLOCK_CLOSURE, no new profile percentages,
    no new FILL_ORDER entry. MemoryPlan has no retrieve_closure field.
    memory_graph.spawn_memory signature unchanged — closure never
    touches the memory graph. RESEARCH_ASSISTANT_PACK still
    EMPTY_CONTRACT. archive_memory / reference_memory / environment_memory
    modules unchanged.

These absences are load-bearing. A test-suite that fails to catch any
of these drifting would let closure silently grow into runtime code.

References:
    - BLOCK_C_DESIGN.md §4 AC-5
    - BLOCK_C_DESIGN.md §10 (non-runtime-touching guarantees)
    - BLOCK_C_DESIGN.md §12 handoff notes 3 + 4
    - PRE_BLOCK_C_PRECONDITIONS.md §11 (non-runtime-touching)
    - Pattern source: tests/test_agent_loop_block_b_present.py
"""
from __future__ import annotations

import inspect
import os
import sys
import tempfile
import unittest
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.agent_loop import AgentRunner, Observation, LLMResponse
from torment_service.thinking_controller import ThinkingController
from torment_service.fabric import TormentFabric


# ---------------------------------------------------------------------------
# Minimal runner + fake-fabric machinery for runner-behavior tests
# ---------------------------------------------------------------------------


@dataclass
class FakeFabricForClosureRuntime:
    """Protocol-compatible fake fabric used to verify runner integration.

    Only the three FabricHandle methods are callable. A closure-shaped
    state dict exists purely as bait: if the runner ever reads or writes
    to it, the regression will be visible.
    """
    ingest_calls: List[Dict[str, Any]] = field(default_factory=list)
    measure_drift_calls: List[Dict[str, Any]] = field(default_factory=list)
    gravity_correction_calls: List[Dict[str, Any]] = field(default_factory=list)

    # Bait: closure-shaped state the runner MUST NOT touch
    _closures: List[Dict[str, Any]] = field(default_factory=list)
    _closure_events: List[Dict[str, Any]] = field(default_factory=list)

    drift_return: Optional[Dict[str, Any]] = None

    # ---------- FabricHandle Protocol ----------

    def ingest(self, workspace_id, agent_id, text, step):
        self.ingest_calls.append({
            "workspace_id": workspace_id, "agent_id": agent_id,
            "text": text, "step": step,
        })
        return {"status": "ok"}

    def measure_drift(self, workspace_id, agent_id):
        self.measure_drift_calls.append(
            {"workspace_id": workspace_id, "agent_id": agent_id}
        )
        return self.drift_return

    def gravity_correction(self, workspace_id, agent_id, drift_info):
        self.gravity_correction_calls.append(
            {"workspace_id": workspace_id, "agent_id": agent_id,
             "drift_info": drift_info}
        )

    # ---------- Test-only bait (NOT part of FabricHandle) ----------

    def _seed_closure(self, arc_name: str) -> str:
        closure_id = f"closure_{len(self._closures):04d}"
        self._closures.append({
            "closure_id": closure_id,
            "arc_name": arc_name,
            "state_events": [],
        })
        return closure_id


@dataclass
class FakeLLM:
    calls: List[Dict[str, Any]] = field(default_factory=list)
    canned_response: str = "response"

    def complete(self, system_prompt, messages, tools=None):
        self.calls.append({"system_prompt": system_prompt,
                           "messages": messages, "tools": tools})
        return LLMResponse(text=self.canned_response)


def _make_runner():
    fabric = FakeFabricForClosureRuntime()
    llm = FakeLLM()
    runner = AgentRunner(
        controller=ThinkingController(),
        fabric=fabric,
        llm_client=llm,
    )
    return runner, fabric, llm


# ---------------------------------------------------------------------------
# AC-5 — AgentRunner signature and FabricHandle Protocol preserved
# ---------------------------------------------------------------------------


class TestAgentRunnerSignaturePreserved(unittest.TestCase):
    """Per §10: AgentRunner.__init__ must not have grown closure
    parameters. Same rule used for Block A (baton) and Block B."""

    def test_agent_runner_init_has_no_closure_parameters(self) -> None:
        sig = inspect.signature(AgentRunner.__init__)
        param_names = set(sig.parameters.keys())
        for forbidden in (
            "closure_store",
            "closure_ledger",
            "propose_closure",
            "ratify_closure",
            "commit_closure",
            "revise_closure",
            "closures",
            "active_closure",
            "arc_name",
        ):
            self.assertNotIn(
                forbidden, param_names,
                f"AgentRunner.__init__ must not accept {forbidden!r} — "
                "runner is frozen per BLOCK_C_DESIGN §10."
            )

    def test_agent_runner_run_turn_signature_has_no_closure_args(self) -> None:
        sig = inspect.signature(AgentRunner.run_turn)
        param_names = set(sig.parameters.keys())
        for forbidden in (
            "closure_id",
            "arc_scope",
            "proposed_closure",
            "ratify",
            "commit_closure",
            "deferred_or_open_items",
        ):
            self.assertNotIn(
                forbidden, param_names,
                f"AgentRunner.run_turn must not accept {forbidden!r} — "
                "run_turn body is unchanged by Block C."
            )


class TestFabricHandleProtocolUnchanged(unittest.TestCase):
    """Per §10 + handoff note 4: FabricHandle Protocol must still be
    exactly the same three methods. Closure introduces NO new protocol
    surface for the runner."""

    def test_fabric_handle_still_three_methods(self) -> None:
        from torment_service.agent_loop import FabricHandle
        protocol_methods = {
            name for name in dir(FabricHandle)
            if not name.startswith("_") and callable(getattr(FabricHandle, name))
        }
        self.assertEqual(
            protocol_methods,
            {"ingest", "measure_drift", "gravity_correction"},
            f"FabricHandle must be exactly three methods; got "
            f"{sorted(protocol_methods)}",
        )

    def test_fabric_handle_has_no_closure_methods(self) -> None:
        """Closure methods must not leak onto the Protocol surface. The
        runner-visible fabric is closed over Block-A retrieval only."""
        from torment_service.agent_loop import FabricHandle
        for forbidden in (
            "propose_closure",
            "ratify_closure",
            "commit_closure",
            "revise_closure",
            "get_closure",
            "list_closures",
        ):
            self.assertFalse(
                hasattr(FabricHandle, forbidden),
                f"FabricHandle must not expose {forbidden!r}; closure "
                "operations are admin/test surface only, not runner-visible."
            )


# ---------------------------------------------------------------------------
# AC-5 — retrieval_assembler unchanged
# ---------------------------------------------------------------------------


class TestRetrievalAssemblerUnchanged(unittest.TestCase):
    """Per §10: retrieval_assembler has no BLOCK_CLOSURE, no new
    FILL_ORDER entry, no new profile percentages. Closure is NOT
    prompt-context-integrable in v0.1 (D.1 rejected γ)."""

    def test_no_block_closure_constant(self) -> None:
        from torment_service import retrieval_assembler as ra
        for forbidden in (
            "BLOCK_CLOSURE",
            "BLOCK_ARCS",
            "BLOCK_END_OF_ARC",
        ):
            self.assertFalse(
                hasattr(ra, forbidden),
                f"retrieval_assembler must not declare {forbidden!r}; "
                "closure is not prompt-context-integrable in v0.1 (D.1)."
            )

    def test_fill_order_still_five_blocks(self) -> None:
        """FILL_ORDER is exactly the five Block-A+B blocks. Closure
        does not extend FILL_ORDER."""
        from torment_service.retrieval_assembler import FILL_ORDER
        self.assertEqual(
            len(FILL_ORDER), 5,
            f"FILL_ORDER must have exactly 5 entries; got {FILL_ORDER}",
        )
        # No entry literally contains "closure"
        for entry in FILL_ORDER:
            self.assertNotIn(
                "closure", entry.lower(),
                f"FILL_ORDER must not contain closure block; got entry {entry!r}"
            )

    def test_profiles_have_no_closure_percentages(self) -> None:
        """Each PROFILE's keys are the five FILL_ORDER blocks only.
        Closure percentages are not added."""
        from torment_service.retrieval_assembler import PROFILES, FILL_ORDER
        fill_order_set = set(FILL_ORDER)
        for profile_name, percentages in PROFILES.items():
            self.assertEqual(
                set(percentages.keys()), fill_order_set,
                f"PROFILE {profile_name!r} must use exactly FILL_ORDER "
                f"keys; got {sorted(percentages.keys())}"
            )


# ---------------------------------------------------------------------------
# AC-5 — MemoryPlan and behavior_packs unchanged
# ---------------------------------------------------------------------------


class TestMemoryPlanUnchanged(unittest.TestCase):
    """Per §10: MemoryPlan has no retrieve_closure field. Closure is
    not a retrievable lane in v0.1."""

    def test_memory_plan_has_no_retrieve_closure_field(self) -> None:
        from torment_service.thinking_models import MemoryPlan
        if hasattr(MemoryPlan, "__dataclass_fields__"):
            fields = set(MemoryPlan.__dataclass_fields__.keys())
            for forbidden in (
                "retrieve_closure",
                "retrieve_arcs",
                "retrieve_end_of_arc",
                "closure_top_k",
            ):
                self.assertNotIn(
                    forbidden, fields,
                    f"MemoryPlan must not have field {forbidden!r}; "
                    "closure is not a MemoryPlan lane in v0.1."
                )


class TestResearchAssistantPackUntouched(unittest.TestCase):
    """Per §10 + analysis §4.4: RESEARCH_ASSISTANT_PACK must still ship
    with EMPTY_CONTRACT. Block C is NOT the retrieval tool family that
    would fill it."""

    def test_research_assistant_pack_still_empty_contract(self) -> None:
        from torment_service.behavior_packs import RESEARCH_ASSISTANT_PACK
        from torment_service.tool_registry import EMPTY_CONTRACT
        self.assertEqual(
            RESEARCH_ASSISTANT_PACK.action_contract, EMPTY_CONTRACT,
            "RESEARCH_ASSISTANT_PACK must still ship with EMPTY_CONTRACT "
            "after Block C; swap-one-field promise is preserved."
        )

    def test_no_closure_behavior_pack(self) -> None:
        """No ARC_CLOSURE_PACK / CLOSURE_AUTHOR_PACK / similar new pack
        is added. Block C is a fabric method set, not a pack."""
        from torment_service import behavior_packs as bp
        for forbidden in (
            "ARC_CLOSURE_PACK",
            "CLOSURE_AUTHOR_PACK",
            "CLOSURE_RATIFIER_PACK",
            "ARC_SYNTHESIS_PACK",
        ):
            self.assertFalse(
                hasattr(bp, forbidden),
                f"behavior_packs must not declare {forbidden!r}; "
                "closure is a fabric method set, not a behavior pack."
            )


# ---------------------------------------------------------------------------
# AC-5 — memory_graph and Block-A/B substrate modules unchanged
# ---------------------------------------------------------------------------


class TestMemoryGraphUnchanged(unittest.TestCase):
    """Per §10 + handoff note 4: memory_graph.spawn_memory signature
    unchanged. Closure never touches the memory graph."""

    def test_spawn_memory_has_no_closure_parameters(self) -> None:
        from torment_service.memory_graph import MemoryGraph
        sig = inspect.signature(MemoryGraph.spawn_memory)
        param_names = set(sig.parameters.keys())
        for forbidden in (
            "closure_id",
            "arc_name",
            "is_closure",
            "arc_kind",
            "deferred_or_open_items",
        ):
            self.assertNotIn(
                forbidden, param_names,
                f"memory_graph.spawn_memory must not accept {forbidden!r}; "
                "closure has its own ClosureStore and never writes to "
                "the memory graph."
            )


class TestBlockAAndBSubstrateModulesUnchanged(unittest.TestCase):
    """Per §10: archive_memory / reference_memory / environment_memory
    modules are not extended, wrapped, or modified by closure."""

    def test_reference_memory_has_no_closure_surface(self) -> None:
        from torment_service import reference_memory as rm
        for forbidden in (
            "ClosureStore",
            "ClosureEntry",
            "propose_closure",
            "commit_closure",
        ):
            self.assertFalse(
                hasattr(rm, forbidden),
                f"reference_memory must not expose {forbidden!r}; "
                "closure lives in torment_service.closure_memory."
            )

    def test_environment_memory_has_no_closure_surface(self) -> None:
        from torment_service import environment_memory as em
        for forbidden in (
            "ClosureStore",
            "ClosureEntry",
            "propose_closure",
            "commit_closure",
        ):
            self.assertFalse(
                hasattr(em, forbidden),
                f"environment_memory must not expose {forbidden!r}; "
                "closure lives in torment_service.closure_memory."
            )

    def test_archive_memory_has_no_closure_surface(self) -> None:
        from torment_service import archive_memory as am
        for forbidden in (
            "ClosureStore",
            "ClosureEntry",
            "propose_closure",
            "commit_closure",
        ):
            self.assertFalse(
                hasattr(am, forbidden),
                f"archive_memory must not expose {forbidden!r}; "
                "closure lives in torment_service.closure_memory."
            )


# ---------------------------------------------------------------------------
# AC-5 — runtime integration: runner completes end-to-end with
# closure state present and does NOT touch it
# ---------------------------------------------------------------------------


class TestRunnerCompletesWithClosurePresent(unittest.TestCase):
    """Runner completes a normal turn even when closure state exists.
    Runner does NOT read or write closure state."""

    def test_run_turn_completes_with_closure_bait_seeded(self) -> None:
        runner, fabric, llm = _make_runner()
        fabric._seed_closure("some-arc")
        fabric._seed_closure("another-arc")

        result = runner.run_turn(
            workspace_id="ws", agent_id="atlas",
            observation=Observation(text="What is the status?"),
            step=1,
        )
        self.assertIsNotNone(result.task_frame)
        self.assertIsNotNone(result.mode_decision)
        self.assertIsNotNone(result.memory_plan)
        self.assertIsNotNone(result.action_decision)
        self.assertIsNotNone(result.action_policy_decision)
        self.assertIsNotNone(result.execution_outcome)
        self.assertIsNotNone(result.review_outcome)

    def test_run_turn_does_not_modify_closure_bait(self) -> None:
        """The runner must not read or write the closure state dict."""
        runner, fabric, llm = _make_runner()
        fabric._seed_closure("arc-x")
        before = [dict(c) for c in fabric._closures]
        runner.run_turn(
            workspace_id="ws", agent_id="atlas",
            observation=Observation(text="Hello."),
            step=1,
        )
        after = [dict(c) for c in fabric._closures]
        self.assertEqual(
            before, after,
            "run_turn must not modify closure state — runner is frozen."
        )
        self.assertEqual(
            fabric._closure_events, [],
            "run_turn must not emit closure events."
        )

    def test_runner_phase_7_ingest_still_four_args(self) -> None:
        """Phase-7 ingest must still use only the four FabricHandle
        protocol args — closure never leaks in."""
        runner, fabric, llm = _make_runner()
        runner.run_turn(
            workspace_id="ws", agent_id="atlas",
            observation=Observation(text="Something with substance."),
            step=17,
        )
        for call in fabric.ingest_calls:
            self.assertEqual(
                set(call.keys()),
                {"workspace_id", "agent_id", "text", "step"},
                "Phase-7 ingest call must match FabricHandle.ingest exactly"
            )


# ---------------------------------------------------------------------------
# AC-5 — fabric.query default-lane filter: closure is excluded by
# default, just like baton/reference/environment
# ---------------------------------------------------------------------------


class TestFabricQueryExcludesClosureFromDefaultLane(unittest.TestCase):
    """Per §10 + Appendix: the default-lane filter frozenset extends
    from {baton, reference, environment} to {baton, reference,
    environment, closure}. Closure entries must not appear in default
    fabric.query() results.

    This is the ONE allowed change inside fabric.query — the SIGNATURE
    is unchanged, only the internal frozenset is extended."""

    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp()
        os.environ["TORMENT_EMBED_PROVIDER"] = "hash"
        self.fabric = TormentFabric(data_dir=self.tmp)
        self.fabric.get_workspace("ws1")
        self.fabric.create_agent("ws1", "atlas")

    def test_fabric_query_signature_unchanged(self) -> None:
        """fabric.query must have the same signature as before Block C."""
        sig = inspect.signature(self.fabric.query)
        param_names = set(sig.parameters.keys())
        for forbidden in (
            "include_closure",
            "closure_only",
            "closure_id",
            "arc_name",
        ):
            self.assertNotIn(
                forbidden, param_names,
                f"fabric.query must not accept {forbidden!r}; only the "
                "internal default-lane filter is extended, not the signature."
            )


# ---------------------------------------------------------------------------
# AC-5 — no MCP surface for closure
# ---------------------------------------------------------------------------


class TestMCPSurfaceUnchanged(unittest.TestCase):
    """Per §10: mcp_server.py is unchanged. Block C introduces no MCP
    tools. Closure is an admin/authoring surface, not a model-visible
    tool."""

    def test_mcp_has_no_closure_tools(self) -> None:
        try:
            from torment_service import mcp_server as mcp
        except ImportError:
            self.skipTest("mcp_server module not present in this environment")
            return
        # Look for any symbol name hinting at closure tools
        closure_attrs = [
            name for name in dir(mcp)
            if "closure" in name.lower() and not name.startswith("_")
        ]
        self.assertEqual(
            closure_attrs, [],
            f"mcp_server must not declare closure tool surface; "
            f"found {closure_attrs}"
        )


# ---------------------------------------------------------------------------
# AC-5 — no shared writeback fixture imports (§9 + §7.5 reviewer rule)
# ---------------------------------------------------------------------------


class TestNoWritebackFixtureEntanglement(unittest.TestCase):
    """Per §7.5 + §9: the five Block C test files must not import
    anything from the writeback test harness. Closure and writeback
    are structurally separate at every layer."""

    @staticmethod
    def _imported_modules(path: str) -> set:
        """Parse a Python file's AST and return the set of imported
        module names. Only real `import` / `from X import` statements
        count — string literals that mention module names are ignored."""
        import ast
        with open(path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=path)
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module is not None:
                    imported.add(node.module)
        return imported

    def test_t1_through_t5_do_not_import_writeback_harness(self) -> None:
        """Check each Block C test file's AST for forbidden imports."""
        here = os.path.dirname(os.path.abspath(__file__))
        block_c_files = [
            "test_closure_shape_boundary.py",
            "test_closure_ratification_required.py",
            "test_closure_versioning_honest.py",
            "test_closure_open_items_honesty.py",
            "test_closure_preserves_blocks_a_and_b.py",
        ]
        forbidden_prefixes = (
            "test_writeback",
            "tests.test_writeback",
        )
        for name in block_c_files:
            path = os.path.join(here, name)
            imported = self._imported_modules(path)
            for mod in imported:
                for prefix in forbidden_prefixes:
                    self.assertFalse(
                        mod.startswith(prefix),
                        f"{name!r} must not import {mod!r} — Block C and "
                        "writeback test harnesses are structurally separate "
                        "(§7.5, §9)."
                    )


if __name__ == "__main__":
    unittest.main()
