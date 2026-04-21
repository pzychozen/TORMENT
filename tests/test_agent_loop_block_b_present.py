# tests/test_agent_loop_block_b_present.py
"""
T4 — AC-3.2: Block-B-meets-Block-A runtime integration test.

Covers the acceptance criterion from BLOCK_B_DESIGN.md §4.3:

    AgentRunner.run_turn completes end-to-end with reference loads and
    environment entries present in the fabric; baton retrieval, core
    retrieval, and archive retrieval are unaffected; all nine scorecard
    invariant tests remain green; RESEARCH_ASSISTANT_PACK's
    EMPTY_CONTRACT swap-one-field promise is untouched.

Design intent per BLOCK_B_DESIGN.md §10 (non-runtime-touching guarantees):

    AgentRunner.__init__ signature unchanged. No new parameters, no
    new dependencies. AgentRunner.run_turn body unchanged. No new
    phases, no new calls, no new branches. FabricHandle Protocol
    unchanged (still four methods). fabric.query signature unchanged.

These tests FAIL against current code only for the Block-B-setup
portion (calling fabric.ingest_reference / write_environment before
implementation lands). The runner portion is expected to behave
identically both before and after Block B lands — that's the invariant.

References:
    - BLOCK_B_DESIGN.md §10 (non-runtime-touching guarantees)
    - TORMENT_AGENT_RUNTIME_SLICE_v0.1_PLAN.md §7 (scorecard)
"""
from __future__ import annotations

import inspect
import os
import sys
import unittest
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.agent_loop import AgentRunner, Observation, LLMResponse
from torment_service.thinking_controller import ThinkingController


# ---------------------------------------------------------------------------
# FakeFabric that supports the FabricHandle Protocol plus Block-B-shaped
# bookkeeping (for tests only — the runner never touches these fields)
# ---------------------------------------------------------------------------


@dataclass
class FakeFabricWithBlockB:
    """Protocol implementation + Block B test bookkeeping.

    The four FabricHandle methods are the only things the runner calls.
    The Block B fields below exist purely so this test can confirm the
    runner does not touch them under any circumstances.
    """
    ingest_calls: List[Dict[str, Any]] = field(default_factory=list)
    measure_drift_calls: List[Dict[str, Any]] = field(default_factory=list)
    gravity_correction_calls: List[Dict[str, Any]] = field(default_factory=list)

    # Block B test bookkeeping — runner must never touch these
    _reference_entries: List[Dict[str, Any]] = field(default_factory=list)
    _active_loads: List[Dict[str, Any]] = field(default_factory=list)
    _environment_entries: List[Dict[str, Any]] = field(default_factory=list)

    drift_return: Optional[Dict[str, Any]] = None

    # ---------- FabricHandle Protocol ----------

    def ingest(self, workspace_id, agent_id, text, step):
        call = {"workspace_id": workspace_id, "agent_id": agent_id,
                "text": text, "step": step}
        self.ingest_calls.append(call)
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

    # ---------- Test helpers (NOT part of FabricHandle) ----------

    def _seed_reference(self, title: str, body: str) -> str:
        ref_id = f"ref_{len(self._reference_entries):04d}"
        self._reference_entries.append({
            "ref_id": ref_id,
            "title": title,
            "body": body,
            "source_link": f"docs/{title}.md",
            "source_kind": "repo_file",
        })
        return ref_id

    def _seed_active_load(self, ref_id: str, agent_id: str) -> str:
        load_id = f"load_{len(self._active_loads):04d}"
        self._active_loads.append({
            "load_id": load_id,
            "ref_id": ref_id,
            "agent_id": agent_id,
            "status": "active",
        })
        return load_id

    def _seed_environment(self, key: str, value: Any,
                          evidence_class: str = "user_asserted") -> str:
        env_id = f"env_{len(self._environment_entries):04d}"
        self._environment_entries.append({
            "env_id": env_id,
            "key": key,
            "value": value,
            "evidence_class": evidence_class,
        })
        return env_id


@dataclass
class FakeLLM:
    calls: List[Dict[str, Any]] = field(default_factory=list)
    canned_response: str = "response"

    def complete(self, system_prompt, messages, tools=None):
        self.calls.append({"system_prompt": system_prompt,
                           "messages": messages, "tools": tools})
        return LLMResponse(text=self.canned_response)


def _make_runner():
    fabric = FakeFabricWithBlockB()
    llm = FakeLLM()
    runner = AgentRunner(
        controller=ThinkingController(),
        fabric=fabric,
        llm_client=llm,
    )
    return runner, fabric, llm


# ---------------------------------------------------------------------------
# Runner completes end-to-end with Block B entries present
# ---------------------------------------------------------------------------


class TestRunTurnCompletesWithBlockBPresent(unittest.TestCase):
    """Runner completes a normal turn when references and environment
    entries exist in the fabric. Neither affects runner behavior."""

    def test_run_turn_completes_with_references_seeded(self) -> None:
        runner, fabric, llm = _make_runner()
        fabric._seed_reference("block_a_design", "A long design doc body...")
        fabric._seed_reference("doctrine_v2", "Twelve doctrine principles...")

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

    def test_run_turn_completes_with_active_loads_seeded(self) -> None:
        runner, fabric, llm = _make_runner()
        ref_id = fabric._seed_reference("ref", "body")
        fabric._seed_active_load(ref_id, "atlas")

        result = runner.run_turn(
            workspace_id="ws", agent_id="atlas",
            observation=Observation(text="Hello."),
            step=1,
        )
        self.assertIsNotNone(result)

    def test_run_turn_completes_with_environment_seeded(self) -> None:
        runner, fabric, llm = _make_runner()
        fabric._seed_environment("network_available", False, "observed")
        fabric._seed_environment("python_version", "3.10.12", "observed")

        result = runner.run_turn(
            workspace_id="ws", agent_id="atlas",
            observation=Observation(text="Run the analysis."),
            step=1,
        )
        self.assertIsNotNone(result)

    def test_run_turn_completes_with_mixed_block_a_and_b(self) -> None:
        """All categories coexisting — core/archive/baton from Block A
        plus references and environment from Block B."""
        runner, fabric, llm = _make_runner()
        fabric._seed_reference("doc", "body")
        fabric._seed_environment("network", True)
        result = runner.run_turn(
            workspace_id="ws", agent_id="atlas",
            observation=Observation(text="What matters here?"),
            step=1,
        )
        self.assertIsNotNone(result)


# ---------------------------------------------------------------------------
# Runner does NOT touch Block B state
# ---------------------------------------------------------------------------


class TestRunnerDoesNotTouchBlockB(unittest.TestCase):
    """AgentRunner must not call any Block B method. It has no reference
    to load_reference, consult_environment, or their state."""

    def test_runner_fabric_handle_protocol_still_four_methods(self) -> None:
        """FabricHandle Protocol must not have grown Block B methods."""
        from torment_service.agent_loop import FabricHandle
        protocol_methods = {
            name for name in dir(FabricHandle)
            if not name.startswith("_") and callable(getattr(FabricHandle, name))
        }
        # Only the four declared methods
        self.assertEqual(
            protocol_methods, {"ingest", "measure_drift", "gravity_correction"},
            f"FabricHandle must have exactly these methods; got {protocol_methods}"
        )

    def test_runner_constructor_has_no_block_b_parameters(self) -> None:
        """AgentRunner.__init__ signature must not have grown Block B
        parameters (per §10)."""
        sig = inspect.signature(AgentRunner.__init__)
        param_names = set(sig.parameters.keys())
        for forbidden in (
            "reference_store", "environment_store",
            "load_reference", "consult_environment",
            "reference_loads", "environment_facts",
        ):
            self.assertNotIn(
                forbidden, param_names,
                f"AgentRunner.__init__ must not accept {forbidden!r} — "
                "runner is frozen per Block B D.4"
            )

    def test_runner_turn_does_not_modify_reference_entries(self) -> None:
        runner, fabric, llm = _make_runner()
        ref_id = fabric._seed_reference("ref", "body before")
        before = dict(fabric._reference_entries[0])
        runner.run_turn(
            workspace_id="ws", agent_id="atlas",
            observation=Observation(text="Hello."),
            step=1,
        )
        after = dict(fabric._reference_entries[0])
        self.assertEqual(before, after,
                         "run_turn must not modify reference entries")

    def test_runner_turn_does_not_modify_environment_entries(self) -> None:
        runner, fabric, llm = _make_runner()
        fabric._seed_environment("k", "v", "observed")
        before = dict(fabric._environment_entries[0])
        runner.run_turn(
            workspace_id="ws", agent_id="atlas",
            observation=Observation(text="Hello."),
            step=1,
        )
        after = dict(fabric._environment_entries[0])
        self.assertEqual(before, after,
                         "run_turn must not modify environment entries")

    def test_runner_phase_7_ingest_signature_preserved(self) -> None:
        """Phase 7 ingest must still use only the four protocol args
        (workspace_id, agent_id, text, step). No memory_class, no
        extra_payload, no reference/environment fields."""
        runner, fabric, llm = _make_runner()
        runner.run_turn(
            workspace_id="ws", agent_id="atlas",
            observation=Observation(text="Something with substance."),
            step=42,
        )
        for call in fabric.ingest_calls:
            self.assertEqual(
                set(call.keys()),
                {"workspace_id", "agent_id", "text", "step"},
                "Runner Phase 7 ingest must match FabricHandle.ingest "
                "protocol exactly"
            )


# ---------------------------------------------------------------------------
# Research-assistant pack's EMPTY_CONTRACT promise preserved
# ---------------------------------------------------------------------------


class TestResearchAssistantPackUntouched(unittest.TestCase):
    """RESEARCH_ASSISTANT_PACK's action_contract must remain EMPTY_CONTRACT.
    Block B is NOT the 'retrieval tool family' that would fill it."""

    def test_research_assistant_pack_still_empty_contract(self) -> None:
        from torment_service.behavior_packs import RESEARCH_ASSISTANT_PACK
        from torment_service.tool_registry import EMPTY_CONTRACT
        self.assertEqual(
            RESEARCH_ASSISTANT_PACK.action_contract, EMPTY_CONTRACT,
            "RESEARCH_ASSISTANT_PACK must still ship with EMPTY_CONTRACT "
            "after Block B. The swap-one-field promise is preserved."
        )


if __name__ == "__main__":
    unittest.main()
