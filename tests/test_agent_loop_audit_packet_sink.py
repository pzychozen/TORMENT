"""Tests for the TurnResult audit packet observation sink (live observation).

AgentRunner.run_turn now composes ``TurnResult.audit_evidence_packet`` via the
inert prompt-inclusion observer ``observe_prompt_inclusion_packet(...)``: the
packet exists ONLY when every supplied admitted item's text is observed in the
captured model-visible request (system_prompt + messages) that produced the FINAL
reviewed response, and a model call occurred this turn. Observation-only:
returned on TurnResult only, never routed into prompt / review / output / ingest /
fabric; packet absence is non-punitive; AgentRunner makes no same-turn provenance
claim.

Behavioral tests use a fake fabric + fake LLM and a review-forcing controller to
pin review outcomes; plus an AST guard on agent_loop.py.
"""

import ast
import os
import unittest
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import torment_service.agent_loop as agent_loop
from torment_service.agent_loop import AgentRunner, Observation
from torment_service.thinking_controller import ThinkingController
from torment_service.thinking_models import ReviewResult
from torment_service.audit_evidence_sidecar import build_audit_evidence_sidecar_from_items


# A sentinel admitted-item text. For the packet to build, this text must appear
# in the captured model-visible request (system prompt + the user message, i.e.
# the observation text) — the caller-owned same-turn inclusion requirement.
_ITEM = "ZZITEM admitted context fact"


def _torment_service_dir():
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(os.path.dirname(here), "torment_service")


@dataclass
class FakeFabric:
    ingest_calls: List[Dict[str, Any]] = field(default_factory=list)
    measure_drift_calls: List[Dict[str, Any]] = field(default_factory=list)
    gravity_correction_calls: List[Dict[str, Any]] = field(default_factory=list)
    drift_return: Optional[Dict[str, Any]] = None

    def ingest(self, workspace_id, agent_id, text, step):
        self.ingest_calls.append({"text": text, "step": step})
        return {"status": "ok"}

    def measure_drift(self, workspace_id, agent_id):
        self.measure_drift_calls.append({"workspace_id": workspace_id})
        return self.drift_return

    def gravity_correction(self, workspace_id, agent_id, drift_info):
        self.gravity_correction_calls.append({"drift_info": drift_info})


@dataclass
class FakeLLM:
    calls: List[Dict[str, Any]] = field(default_factory=list)
    canned_response: str = "A clean reply."

    def complete(self, system_prompt, messages, tools=None):
        from torment_service.agent_loop import LLMResponse
        self.calls.append({"system_prompt": system_prompt, "messages": messages})
        return LLMResponse(text=self.canned_response)


class _Controller(ThinkingController):
    """Real deliberation; review may be forced and its input recorded."""

    def __init__(self, forced_review=None):
        super().__init__()
        self.forced_review = forced_review
        self.review_drafts: List[Any] = []

    def review(self, *, frame, mode, action, response_draft):
        self.review_drafts.append(response_draft)
        if self.forced_review is not None:
            return self.forced_review
        return super().review(frame=frame, mode=mode, action=action,
                              response_draft=response_draft)


def _make_runner(forced_review=None, canned="A clean reply."):
    fabric = FakeFabric()
    llm = FakeLLM(canned_response=canned)
    controller = _Controller(forced_review=forced_review)
    runner = AgentRunner(controller=controller, fabric=fabric, llm_client=llm)
    return runner, fabric, llm, controller


def _items(text=_ITEM):
    return [{"eid": 1, "block_type": "relational_context", "text": text}]


# An observation whose text contains the item text (so inclusion is observed in
# the captured model-visible request).
def _obs_including_item(text=_ITEM):
    return Observation(text=f"Please consider: {text} — tell me more.")


class TestPacketBuild(unittest.TestCase):

    def test_default_packet_is_none(self):
        runner, _, _, _ = _make_runner()
        result = runner.run_turn(
            workspace_id="ws", agent_id="agent",
            observation=_obs_including_item(), step=1,
        )
        self.assertIsNone(result.audit_evidence_packet)

    def test_packet_builds_when_item_observed_in_prompt(self):
        forced = ReviewResult(approved=True, revised=True, revised_text="FINALZZ clean")
        runner, _, _, _ = _make_runner(forced_review=forced)
        result = runner.run_turn(
            workspace_id="ws", agent_id="agent",
            observation=_obs_including_item(), step=1,
            audit_admitted_context_items=_items(),
        )
        pkt = result.audit_evidence_packet
        self.assertIsNotNone(pkt)
        self.assertEqual(pkt["response_text"], "FINALZZ clean")
        self.assertIn("evidence_items", pkt)

    def test_item_absent_from_prompt_yields_none_turn_proceeds(self):
        forced = ReviewResult(approved=True, revised=True, revised_text="a reply")
        runner, fabric, _, _ = _make_runner(forced_review=forced)
        result = runner.run_turn(
            workspace_id="ws", agent_id="agent",
            observation=Observation(text="an unrelated benign question"), step=1,
            audit_admitted_context_items=_items(),  # item text NOT in the observation
        )
        self.assertIsNone(result.audit_evidence_packet)
        # Response/review/ingest/stabilize still proceeded.
        self.assertEqual(result.execution_outcome.response_text, "a reply")
        self.assertEqual(len(fabric.measure_drift_calls), 1)

    def test_review_revised_text_used_not_draft(self):
        forced = ReviewResult(approved=True, revised=True, revised_text="REVISEDZZ final")
        runner, _, _, _ = _make_runner(forced_review=forced, canned="DRAFTZZ original")
        result = runner.run_turn(
            workspace_id="ws", agent_id="agent",
            observation=_obs_including_item(), step=1,
            audit_admitted_context_items=_items(),
        )
        pkt = result.audit_evidence_packet
        self.assertIsNotNone(pkt)
        self.assertEqual(pkt["response_text"], "REVISEDZZ final")
        self.assertNotIn("DRAFTZZ", pkt["response_text"])

    def test_review_blocked_yields_no_packet(self):
        forced = ReviewResult(approved=False, blocked=True)
        runner, _, _, _ = _make_runner(forced_review=forced)
        result = runner.run_turn(
            workspace_id="ws", agent_id="agent",
            observation=_obs_including_item(), step=1,
            audit_admitted_context_items=_items(),
        )
        self.assertIsNone(result.audit_evidence_packet)
        self.assertIsNone(result.execution_outcome.response_text)

    def test_empty_response_text_yields_no_packet(self):
        forced = ReviewResult(approved=True, revised=True, revised_text="")
        runner, _, _, _ = _make_runner(forced_review=forced)
        result = runner.run_turn(
            workspace_id="ws", agent_id="agent",
            observation=_obs_including_item(), step=1,
            audit_admitted_context_items=_items(),
        )
        self.assertIsNone(result.audit_evidence_packet)

    def test_observer_exception_is_fail_soft(self):
        forced = ReviewResult(approved=True, revised=True, revised_text="X reply")
        runner, fabric, _, _ = _make_runner(forced_review=forced)
        orig = agent_loop.observe_prompt_inclusion_packet

        def _boom(*a, **k):
            raise RuntimeError("boom")

        agent_loop.observe_prompt_inclusion_packet = _boom
        try:
            result = runner.run_turn(
                workspace_id="ws", agent_id="agent",
                observation=_obs_including_item(), step=1,
                audit_admitted_context_items=_items(),
            )
        finally:
            agent_loop.observe_prompt_inclusion_packet = orig
        # Fail-soft: packet None, turn still completed (Phase 8 ran).
        self.assertIsNone(result.audit_evidence_packet)
        self.assertEqual(len(fabric.measure_drift_calls), 1)


class TestAuditItemsDoNotLeak(unittest.TestCase):

    def test_audit_items_not_injected_into_prompt_review_ingest_fabric(self):
        # An item whose text is NOT in the observation: run_turn must not inject
        # the audit items anywhere (prompt/review/ingest/fabric), and the packet
        # is omitted (inclusion not observed).
        sentinel = "ZZNOLEAK secret admitted note"
        forced = ReviewResult(approved=True, revised=True, revised_text="clean reply")
        runner, fabric, llm, controller = _make_runner(forced_review=forced)
        result = runner.run_turn(
            workspace_id="ws", agent_id="agent",
            observation=Observation(text="a benign user question"), step=7,
            audit_admitted_context_items=_items(text=sentinel),
        )
        for call in llm.calls:
            self.assertNotIn(sentinel, str(call.get("system_prompt", "")))
            self.assertNotIn(sentinel, str(call.get("messages", "")))
        self.assertNotIn(sentinel, str(controller.review_drafts))
        for call in fabric.ingest_calls:
            self.assertNotIn(sentinel, str(call.get("text", "")))
        self.assertNotIn(sentinel, str(fabric.measure_drift_calls))
        self.assertNotIn(sentinel, str(fabric.gravity_correction_calls))
        self.assertNotIn(sentinel, (result.execution_outcome.response_text or ""))
        self.assertNotIn(sentinel, str(result.metadata))
        self.assertFalse(hasattr(result.execution_outcome, "audit_evidence_packet"))
        self.assertIsNone(result.audit_evidence_packet)


class TestSourceGuard(unittest.TestCase):

    def test_agent_loop_sink_goes_through_observer_not_direct_sidecar(self):
        path = os.path.join(_torment_service_dir(), "agent_loop.py")
        with open(path, "r", encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        import_leaves = set()
        imported_names = set()
        call_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for n in node.names:
                    import_leaves.add(n.name.split(".")[-1])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    import_leaves.add(node.module.split(".")[-1])
                for n in node.names:
                    imported_names.add(n.name)
            elif isinstance(node, ast.Call):
                f = node.func
                call_names.add(
                    f.id if isinstance(f, ast.Name)
                    else f.attr if isinstance(f, ast.Attribute) else ""
                )
        # The sink now goes through the inert observer, imported and called.
        self.assertIn("observe_prompt_inclusion_packet", imported_names)
        self.assertIn("observe_prompt_inclusion_packet", call_names)
        # No longer directly imports/calls the sidecar item-core for this sink.
        self.assertNotIn("build_audit_evidence_sidecar_from_items", imported_names)
        self.assertNotIn("build_audit_evidence_sidecar_from_items", call_names)
        # Forbidden modules/builders still absent.
        self.assertNotIn("build_audit_evidence_sidecar_from_assembled_context", imported_names)
        for forbidden in ("audit_evidence_context", "audit_evidence_packet",
                          "retrieval_assembler"):
            self.assertNotIn(forbidden, import_leaves,
                             msg=f"agent_loop.py imports forbidden module: {forbidden}")
        for bad in ("assemble_context", "selected_admitted_items",
                    "build_audit_evidence_packet",
                    "build_audit_evidence_sidecar_from_assembled_context"):
            self.assertNotIn(bad, call_names,
                             msg=f"agent_loop.py calls forbidden builder: {bad}")


if __name__ == "__main__":
    unittest.main()
