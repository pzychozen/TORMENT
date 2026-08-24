"""Focused proof for the private selected-items runner bridge (this slice).

Bridge under test: ``torment_service/audit_selected_items_runner_bridge.py`` ::
``run_turn_with_selected_items_observation`` -- the first authorized private
bridge that forwards the assembler-SELECTED admitted item dicts of an explicit,
caller-supplied ``AssembledContext`` into the existing observation-only audit
seam ``AgentRunner.run_turn(..., audit_admitted_context_items=...)``.

Doctrine: memory may shape context but may not seize authority; audit observes
authority and must not become authority. The bridge is observation-only and
confers no control.

Proves the eight required properties:
  1. The bridge extracts selected items from the EXACT same AssembledContext it
     receives (same dict object identity).
  2. The bridge forwards ONLY selected item dicts, never the whole
     AssembledContext.
  3. The bridge does not mutate the AssembledContext.
  4. No endpoint / schema / public API is introduced (closed import surface; no
     decorators; no schema classes; app.py does not import the bridge).
  5. No prompt-path injection (a supplied item's text absent from the
     observation never reaches the model-visible prompt / review / ingest).
  6. Packet presence vs absence is consumed by nothing (output / review / ingest
     / fabric identical whether or not a packet is produced).
  7. Items whose text is absent from the captured prompt yield
     ``TurnResult.audit_evidence_packet is None`` (non-punitive).
  8. The bridge stays private / internal / observation-only (closed import
     surface, called nowhere in the service package, no authority/claim flags).

Plus a positive companion: when a selected item's text IS in the prompt, the
bridge feeds it through the REAL observer path and a bounded packet results --
the existing observation-only surface, no new ``TurnResult`` field.

Tests-only. Adds no production wiring beyond the bridge module itself.
"""

import ast
import copy
import os
import unittest
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from torment_service.audit_selected_items_runner_bridge import (
    run_turn_with_selected_items_observation,
)
from torment_service.audit_evidence_context import selected_admitted_items
from torment_service.retrieval_assembler import AssembledContext
from torment_service.agent_loop import AgentRunner, Observation
from torment_service.thinking_controller import ThinkingController
from torment_service.thinking_models import ReviewResult


_BRIDGE_MODULE = "audit_selected_items_runner_bridge.py"
# Closed import surface for the bridge: only the pure extractor + stdlib typing.
_ALLOWED_BRIDGE_IMPORT_LEAVES = {"__future__", "typing", "audit_evidence_context"}
# Mirror of the characterization file's quoted guard list.
_FORBIDDEN_FLAGS = {
    "same_turn_verified", "verified", "truth", "authority",
    "trusted", "certified", "honest",
}


# --------------------------------------------------------------------------- #
# AST helpers (mirror the characterization file's conventions)
# --------------------------------------------------------------------------- #

def _torment_service_dir():
    here = os.path.dirname(os.path.abspath(__file__))            # tests/
    return os.path.join(os.path.dirname(here), "torment_service")


def _parse_service(filename):
    with open(os.path.join(_torment_service_dir(), filename), "rb") as fh:
        # null-strip tolerates a mount-corruption artifact in some sandboxes;
        # the authoritative Windows repo parses cleanly.
        return ast.parse(fh.read().replace(b"\x00", b""))


def _iter_service_trees():
    svc = _torment_service_dir()
    for fn in sorted(os.listdir(svc)):
        if not fn.endswith(".py"):
            continue
        try:
            yield fn, _parse_service(fn)
        except (SyntaxError, ValueError):
            continue


def _import_leaves_names(tree):
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


# --------------------------------------------------------------------------- #
# Behavioral fixtures (mirror the characterization / packet-sink test files)
# --------------------------------------------------------------------------- #

@dataclass
class _FakeFabric:
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
class _FakeLLM:
    calls: List[Dict[str, Any]] = field(default_factory=list)
    canned_response: str = "A clean reply."

    def complete(self, system_prompt, messages, tools=None):
        from torment_service.agent_loop import LLMResponse
        self.calls.append({"system_prompt": system_prompt, "messages": messages})
        return LLMResponse(text=self.canned_response)


class _ForcedReview(ThinkingController):
    def __init__(self, forced):
        super().__init__()
        self._forced = forced
        self.review_drafts: List[Any] = []

    def review(self, *args, **kwargs):
        expected = {"frame", "mode", "action", "response_draft"}
        if args or set(kwargs) != expected:
            raise AssertionError("AgentRunner review must use named arguments")
        self.review_drafts.append(kwargs["response_draft"])
        return self._forced


class _SpyRunner:
    """Records exactly what the bridge forwards, without running a real turn.

    The bridge must NOT read anything off the returned object, so a return value
    with no audit attributes is a sufficient stand-in for a ``TurnResult``."""

    def __init__(self):
        self.calls: List[Dict[str, Any]] = []

    def run_turn(self, *, workspace_id, agent_id, observation, step,
                 audit_admitted_context_items=None):
        self.calls.append({
            "workspace_id": workspace_id,
            "agent_id": agent_id,
            "observation": observation,
            "step": step,
            "audit_admitted_context_items": audit_admitted_context_items,
        })
        return object()


_TOKEN = "QZX_SELECTED_ITEM_TOKEN"
_OBS_WITH_TOKEN = f"a benign question mentioning {_TOKEN} inline"
_OBS_PLAIN = "a benign question with nothing notable"
_ABSENT_TEXT = "ZZABSENT selected item text not present in the observation"
_UNSELECTED_TEXT = "an unselected core block"


def _assembled(selected_text, unselected_text=_UNSELECTED_TEXT):
    """An explicit AssembledContext with one SELECTED relational block and one
    UNSELECTED core block (present in ``blocks`` but not marked selected)."""
    ac = AssembledContext(profile="default", token_budget=1000)
    ac.blocks = {
        "relational_context": [
            {"block_type": "relational_context", "eid": 1, "chunk_id": None,
             "text": selected_text},
        ],
        "core_context": [
            {"block_type": "core_context", "eid": 2, "chunk_id": None,
             "text": unselected_text},
        ],
    }
    ac.selection_log = [
        {"action": "selected", "block_type": "relational_context",
         "eid": 1, "chunk_id": None},
        {"action": "skipped", "block_type": "core_context",
         "eid": 2, "chunk_id": None},
    ]
    return ac


def _real_runner():
    fabric = _FakeFabric()
    controller = _ForcedReview(ReviewResult(approved=True, revised=True,
                                            revised_text="a reviewed reply"))
    llm = _FakeLLM()
    runner = AgentRunner(controller=controller, fabric=fabric, llm_client=llm)
    return runner, fabric, controller, llm


# --------------------------------------------------------------------------- #
# 1-3: extraction / forwarding / non-mutation (spy runner)
# --------------------------------------------------------------------------- #

class TestBridgeExtractionAndForwarding(unittest.TestCase):

    def test_extracts_selected_items_from_same_assembled_context(self):
        # Property 1.
        ac = _assembled(_TOKEN)
        spy = _SpyRunner()
        run_turn_with_selected_items_observation(
            spy, ac, workspace_id="ws", agent_id="agent",
            observation=Observation(text=_OBS_WITH_TOKEN), step=1,
        )
        forwarded = spy.calls[0]["audit_admitted_context_items"]
        # Same items the pure extractor returns for THIS object...
        self.assertEqual(forwarded, selected_admitted_items(ac))
        # ...and they are the very dict objects living in this AssembledContext
        # (sourced from the exact object received, not rebuilt or refetched).
        self.assertIs(forwarded[0], ac.blocks["relational_context"][0])

    def test_forwards_only_selected_item_dicts_never_whole_context(self):
        # Property 2.
        ac = _assembled(_TOKEN)
        spy = _SpyRunner()
        run_turn_with_selected_items_observation(
            spy, ac, workspace_id="ws", agent_id="agent",
            observation=Observation(text=_OBS_WITH_TOKEN), step=1,
        )
        forwarded = spy.calls[0]["audit_admitted_context_items"]
        # Never the AssembledContext object itself.
        self.assertNotIsInstance(forwarded, AssembledContext)
        self.assertIsInstance(forwarded, list)
        self.assertTrue(all(isinstance(x, dict) for x in forwarded))
        # Only the SELECTED block; the unselected core block is excluded.
        self.assertEqual(len(forwarded), 1)
        self.assertEqual(forwarded[0].get("eid"), 1)
        blob = str(forwarded)
        self.assertIn(_TOKEN, blob)
        self.assertNotIn(_UNSELECTED_TEXT, blob)

    def test_does_not_mutate_assembled_context(self):
        # Property 3.
        ac = _assembled(_TOKEN)
        before = copy.deepcopy(ac.to_dict())
        spy = _SpyRunner()
        run_turn_with_selected_items_observation(
            spy, ac, workspace_id="ws", agent_id="agent",
            observation=Observation(text=_OBS_WITH_TOKEN), step=1,
        )
        self.assertEqual(ac.to_dict(), before)


# --------------------------------------------------------------------------- #
# 4 & 8: no endpoint/schema/API; private / observation-only (AST + topology)
# --------------------------------------------------------------------------- #

class TestBridgeIsPrivateNonEndpoint(unittest.TestCase):

    def setUp(self):
        self.bridge = _parse_service(_BRIDGE_MODULE)

    def test_closed_import_surface(self):
        # Properties 4 & 8: imports no app / endpoint / schema / model / writer /
        # persistence / assembler / agent_loop module.
        leaves, _ = _import_leaves_names(self.bridge)
        extra = leaves - _ALLOWED_BRIDGE_IMPORT_LEAVES
        self.assertEqual(
            extra, set(),
            msg=f"bridge imports outside the allowed surface: {sorted(extra)}",
        )

    def test_no_endpoint_decorators_or_schema_classes(self):
        # Property 4: no decorated functions (no @app.route / @router.* endpoint)
        # and no class definitions (no request/response schema models).
        decorated = [n.name for n in ast.walk(self.bridge)
                     if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                     and n.decorator_list]
        classes = [n.name for n in ast.walk(self.bridge)
                   if isinstance(n, ast.ClassDef)]
        self.assertEqual(decorated, [], msg=f"bridge has decorated fn(s): {decorated}")
        self.assertEqual(classes, [], msg=f"bridge defines class(es)/schema: {classes}")

    def test_app_does_not_import_the_bridge(self):
        # Property 4: no endpoint wiring -- app.py does not import the bridge.
        leaves, names = _import_leaves_names(_parse_service("app.py"))
        self.assertNotIn("audit_selected_items_runner_bridge", leaves)
        self.assertNotIn("run_turn_with_selected_items_observation", names)

    def test_bridge_is_called_nowhere_in_service_package(self):
        # Property 8: observation-only dead-end -- no service module imports the
        # bridge module or its function (only tests do).
        importers = []
        for fn, tree in _iter_service_trees():
            if fn == _BRIDGE_MODULE:
                continue
            leaves, names = _import_leaves_names(tree)
            if ("audit_selected_items_runner_bridge" in leaves
                    or "run_turn_with_selected_items_observation" in names):
                importers.append(fn)
        self.assertEqual(importers, [], msg=f"bridge is wired into: {importers}")

    def test_no_forbidden_authority_or_claim_flag(self):
        # Property 8: no authority / proof / claim flag in bridge identifiers.
        offenders = _idents(self.bridge) & _FORBIDDEN_FLAGS
        self.assertEqual(
            offenders, set(),
            msg=f"forbidden flag in bridge identifiers: {sorted(offenders)}",
        )


# --------------------------------------------------------------------------- #
# 5: no prompt-path injection (real runner + fakes)
# --------------------------------------------------------------------------- #

class TestBridgeNoPromptInjection(unittest.TestCase):

    def test_supplied_item_text_never_enters_prompt_review_or_ingest(self):
        # Property 5. The bridge forwards a selected item whose text is NOT in the
        # observation; that text must never appear in the model-visible prompt,
        # the review input, or the ingest text (the bridge injects nothing).
        ac = _assembled(_ABSENT_TEXT)
        runner, fabric, controller, llm = _real_runner()
        result = run_turn_with_selected_items_observation(
            runner, ac, workspace_id="ws", agent_id="agent",
            observation=Observation(text=_OBS_PLAIN), step=1,
        )
        for call in llm.calls:
            self.assertNotIn(_ABSENT_TEXT, str(call.get("system_prompt", "")))
            self.assertNotIn(_ABSENT_TEXT, str(call.get("messages", "")))
        self.assertNotIn(_ABSENT_TEXT, str(controller.review_drafts))
        for call in fabric.ingest_calls:
            self.assertNotIn(_ABSENT_TEXT, str(call.get("text", "")))
        self.assertNotIn(_ABSENT_TEXT, str(fabric.measure_drift_calls))
        self.assertNotIn(_ABSENT_TEXT, str(fabric.gravity_correction_calls))
        self.assertNotIn(_ABSENT_TEXT, (result.execution_outcome.response_text or ""))
        self.assertNotIn(_ABSENT_TEXT, str(result.metadata))


# --------------------------------------------------------------------------- #
# 7: absent items -> None packet, non-punitive (real runner + fakes)
# --------------------------------------------------------------------------- #

class TestBridgeAbsentItemsYieldNoPacket(unittest.TestCase):

    def test_absent_items_yield_none_packet_and_normal_response(self):
        # Property 7.
        ac = _assembled(_ABSENT_TEXT)
        runner, fabric, controller, llm = _real_runner()
        result = run_turn_with_selected_items_observation(
            runner, ac, workspace_id="ws", agent_id="agent",
            observation=Observation(text=_OBS_PLAIN), step=1,
        )
        self.assertIsNone(result.audit_evidence_packet)
        # Non-punitive: the normal reviewed response still came through.
        self.assertEqual(result.execution_outcome.response_text, "a reviewed reply")


# --------------------------------------------------------------------------- #
# 6 + positive companion: packet presence is non-control (real runner + fakes)
# --------------------------------------------------------------------------- #

class TestBridgePacketPresenceIsNonControl(unittest.TestCase):

    def test_present_item_feeds_observer_and_yields_packet(self):
        # Positive path: a selected item whose text IS in the prompt flows through
        # the REAL observer seam and a bounded packet results -- proving the
        # bridge actually feeds real selected item dicts into the existing
        # observer path (the packet is the existing observation-only surface).
        ac = _assembled(_TOKEN)
        runner, fabric, controller, llm = _real_runner()
        result = run_turn_with_selected_items_observation(
            runner, ac, workspace_id="ws", agent_id="agent",
            observation=Observation(text=_OBS_WITH_TOKEN), step=1,
        )
        # Precondition: the selected token reaches the captured model-visible prompt.
        self.assertTrue(
            any(_TOKEN in str(c.get("messages", "")) for c in llm.calls),
            "precondition: selected token must be in the captured prompt",
        )
        packet = result.audit_evidence_packet
        self.assertIsNotNone(packet)
        self.assertIn("response_text", packet)
        self.assertIn("evidence_items", packet)

    def test_packet_presence_vs_absence_changes_no_downstream_behavior(self):
        # Property 6. Hold the observation constant. Run A supplies selected items
        # via the bridge (token present -> packet produced). Run B runs the same
        # turn with NO audit items (packet absent). Output / review / ingest /
        # fabric are identical; only ``audit_evidence_packet`` differs (dict vs
        # None). Packet presence/absence is consumed by nothing.
        ac = _assembled(_TOKEN)
        runner_a, fabric_a, controller_a, llm_a = _real_runner()
        res_a = run_turn_with_selected_items_observation(
            runner_a, ac, workspace_id="ws", agent_id="agent",
            observation=Observation(text=_OBS_WITH_TOKEN), step=1,
        )

        runner_b, fabric_b, controller_b, llm_b = _real_runner()
        res_b = runner_b.run_turn(
            workspace_id="ws", agent_id="agent",
            observation=Observation(text=_OBS_WITH_TOKEN), step=1,
        )

        # The only difference is the observation-only packet.
        self.assertIsNotNone(res_a.audit_evidence_packet)
        self.assertIsNone(res_b.audit_evidence_packet)

        # Output / review / ingest / fabric are unchanged by packet presence.
        self.assertEqual(res_a.execution_outcome.response_text,
                         res_b.execution_outcome.response_text)
        self.assertEqual(controller_a.review_drafts, controller_b.review_drafts)
        self.assertEqual(fabric_a.ingest_calls, fabric_b.ingest_calls)
        self.assertEqual(len(fabric_a.measure_drift_calls),
                         len(fabric_b.measure_drift_calls))
        self.assertEqual(fabric_a.gravity_correction_calls,
                         fabric_b.gravity_correction_calls)


if __name__ == "__main__":
    unittest.main()
