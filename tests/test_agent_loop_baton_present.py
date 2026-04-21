# tests/test_agent_loop_baton_present.py
"""
T3 — AC-5 proof: AgentRunner.run_turn completes end-to-end with baton
entries in the substrate. Runtime integration test.

Covers the acceptance criterion from BLOCK_A_DESIGN.md §4 AC-5:

    Runtime integration unchanged. AgentRunner.run_turn completes
    end-to-end with baton entries present in the substrate; all nine
    scorecard invariant tests from the runtime slice plan continue to
    pass. Baton-specific behavior is driven entirely by provenance and
    memory_class fields; no runner branching is added.

Design intent per BLOCK_A_DESIGN.md §9 (SessionLifecycleHook):
    AgentRunner has NO knowledge of memory_class or baton lifecycle.
    Phase 7 `fabric.ingest(workspace_id, agent_id, text, step)` remains
    signature-limited per the FabricHandle Protocol. Baton writes happen
    through the direct fabric API outside run_turn. This test verifies
    that presence of baton entries in the fabric does not alter the
    runner's phase traversal or TurnResult shape.

These tests FAIL against current code only for the baton-setup portion
(fabric.ingest with memory_class="baton" will currently not validate
the lifecycle). The runner portion is expected to work identically
both before and after baton support lands — that's the invariant.

References:
    - BLOCK_A_DESIGN.md §4 AC-5
    - BLOCK_A_DESIGN.md §9 (SessionLifecycleHook declaration, no wiring)
    - TORMENT_AGENT_RUNTIME_SLICE_v0.1_PLAN.md §7 (scorecard invariants)
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.agent_loop import AgentRunner, Observation, LLMResponse
from torment_service.thinking_controller import ThinkingController
from torment_service.provenance_v1 import ProvenanceV1


# ---------------------------------------------------------------------------
# Fake fabric that records ingest calls AND tracks "pre-existing" baton
# entries. Runner should not touch baton state — this fake exists to
# confirm that.
# ---------------------------------------------------------------------------


@dataclass
class FakeFabricWithBatons:
    """Test double for FabricHandle that also tracks baton-shaped state.

    Note: the FabricHandle protocol only declares ingest/measure_drift/
    gravity_correction. The runner never calls list_active_batons or
    resolve_baton. This fake has those methods for test-local setup
    only — the runner will never invoke them.
    """
    ingest_calls: List[Dict[str, Any]] = field(default_factory=list)
    measure_drift_calls: List[Dict[str, Any]] = field(default_factory=list)
    gravity_correction_calls: List[Dict[str, Any]] = field(default_factory=list)
    # Local baton bookkeeping — not touched by AgentRunner.
    _baton_entries: List[Dict[str, Any]] = field(default_factory=list)
    drift_return: Optional[Dict[str, Any]] = None

    def ingest(self, workspace_id, agent_id, text, step):
        """FabricHandle.ingest signature: (workspace_id, agent_id, text, step).
        Note there is NO memory_class or extra_payload parameter — the
        runner does not have a way to express baton-class writes."""
        call = {
            "workspace_id": workspace_id,
            "agent_id": agent_id,
            "text": text,
            "step": step,
        }
        self.ingest_calls.append(call)
        return {"status": "ok"}

    def measure_drift(self, workspace_id, agent_id):
        self.measure_drift_calls.append(
            {"workspace_id": workspace_id, "agent_id": agent_id}
        )
        return self.drift_return

    def gravity_correction(self, workspace_id, agent_id, drift_info):
        self.gravity_correction_calls.append(
            {"workspace_id": workspace_id,
             "agent_id": agent_id,
             "drift_info": drift_info}
        )

    # Test-local helper — NOT part of FabricHandle protocol
    def _seed_baton(self, text: str, owner: str = "user") -> int:
        eid = len(self._baton_entries) + 1000  # synthetic eid
        self._baton_entries.append({
            "eid": eid,
            "text": text,
            "memory_class": "baton",
            "baton_lifecycle": {
                "owner": owner,
                "expires_when": "later",
                "resolution_condition": "attended",
                "status": "active",
            },
        })
        return eid


@dataclass
class FakeLLM:
    calls: List[Dict[str, Any]] = field(default_factory=list)
    canned_response: str = "A response."

    def complete(self, system_prompt, messages, tools=None):
        self.calls.append({"system_prompt": system_prompt,
                           "messages": messages, "tools": tools})
        return LLMResponse(text=self.canned_response)


def _make_runner():
    fabric = FakeFabricWithBatons()
    llm = FakeLLM()
    runner = AgentRunner(
        controller=ThinkingController(),
        fabric=fabric,
        llm_client=llm,
    )
    return runner, fabric, llm


class TestRunTurnCompletesWithBatonEntriesPresent(unittest.TestCase):
    """AgentRunner.run_turn must complete normally with baton entries
    already present in the fabric. The runner does not branch on
    memory_class."""

    def test_run_turn_completes_with_batons_seeded(self) -> None:
        runner, fabric, llm = _make_runner()
        # Seed some batons BEFORE the turn runs
        fabric._seed_baton("Remember to check the migration script.")
        fabric._seed_baton("Follow up with alice about the api proposal.",
                            owner="next_ai")
        self.assertEqual(len(fabric._baton_entries), 2)

        result = runner.run_turn(
            workspace_id="ws", agent_id="atlas",
            observation=Observation(text="What is the status?"),
            step=1,
        )

        # TurnResult is populated — every phase ran
        self.assertIsNotNone(result.task_frame)
        self.assertIsNotNone(result.mode_decision)
        self.assertIsNotNone(result.memory_plan)
        self.assertIsNotNone(result.action_decision)
        self.assertIsNotNone(result.action_policy_decision)
        self.assertIsNotNone(result.execution_outcome)
        self.assertIsNotNone(result.review_outcome)
        self.assertIsInstance(result.assimilation_outcomes, list)

    def test_run_turn_ingest_does_not_carry_memory_class(self) -> None:
        """Phase 7 ingest signature is FabricHandle.ingest(ws, agent, text, step).
        There is no memory_class parameter — the runner never does a
        baton write. This pins the 'no runner branching for baton' rule."""
        runner, fabric, llm = _make_runner()
        runner.run_turn(
            workspace_id="ws", agent_id="atlas",
            observation=Observation(text="Tell me about the plan."),
            step=42,
        )
        # If any ingest happened, it used only the four protocol args
        for call in fabric.ingest_calls:
            self.assertEqual(
                set(call.keys()),
                {"workspace_id", "agent_id", "text", "step"},
                "Runner's Phase 7 ingest must match FabricHandle.ingest "
                "protocol exactly — no memory_class, no extra_payload"
            )

    def test_baton_entries_not_modified_by_run_turn(self) -> None:
        """Runner does not touch baton state. Same entries before/after."""
        runner, fabric, llm = _make_runner()
        baton_eid = fabric._seed_baton("Check the auth migration.")
        before = dict(fabric._baton_entries[0])

        runner.run_turn(
            workspace_id="ws", agent_id="atlas",
            observation=Observation(text="Hello."),
            step=1,
        )

        after = dict(fabric._baton_entries[0])
        self.assertEqual(before, after,
                         "run_turn must not modify baton entries")


class TestSessionLifecycleHookNotWired(unittest.TestCase):
    """Per D.2 + §9: SessionLifecycleHook Protocol is declared but NOT
    wired to AgentRunner. The runner's __init__ must not accept a hook
    parameter, and run_turn must not call any on_session_* method."""

    def test_agent_runner_constructor_has_no_hook_parameter(self) -> None:
        import inspect
        sig = inspect.signature(AgentRunner.__init__)
        param_names = set(sig.parameters.keys())
        for forbidden in ("session_hook", "lifecycle_hook",
                          "session_lifecycle_hook", "hook"):
            self.assertNotIn(
                forbidden, param_names,
                f"AgentRunner.__init__ must not accept {forbidden!r} — "
                "SessionLifecycleHook is declared only, not wired"
            )


if __name__ == "__main__":
    unittest.main()
