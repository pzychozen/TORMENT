"""Regression tests for Spine escalation_reasons wiring.

Verifies that submit_task() always produces a concrete list for
escalation_reasons in the SpineResponse, never a function object.

Root cause: line ~1320 of spine.py referenced the module-level function
``escalation_reasons`` instead of the local variable ``esc_reasons``,
causing ``list(escalation_reasons)`` to throw
``TypeError: 'function' object is not iterable``.
"""
import os
import sys
import traceback
from unittest.mock import MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def _make_mock_fabric():
    """Build a minimal mock fabric for submit_task()."""
    fabric = MagicMock()
    # get_workspace returns an object with shared_graphs
    ws = MagicMock()
    ws.shared_graphs = {"default": MagicMock()}
    fabric.get_workspace.return_value = ws
    # character_store.load_state returns None
    fabric.character_store.load_state.return_value = None
    # ingest returns a dict with an eid
    fabric.ingest.return_value = {"eid": 1, "domain_id": "default"}
    return fabric


def _make_ctx():
    """Build a minimal RequestContext."""
    from torment_service.request_context import RequestContext
    return RequestContext(
        client_id="test_client",
        trust_tier=1.0,
        workspace_id="ws_test",
        agent_id="ag_test",
    )


class TestEscalationReasonsIsList:

    def test_submit_task_escalation_reasons_is_list_not_callable(self):
        """escalation_reasons in SpineResponse must be a list, not a
        function object. This is the exact regression for the TypeError
        on /agent/ingest."""
        from torment_service.spine import submit_task, SpineRequest

        fabric = _make_mock_fabric()
        ctx = _make_ctx()
        req = SpineRequest(
            workspace_id="ws_test",
            agent_id="ag_test",
            operation="ingest",
            payload={"text": "hello world", "step": 1},
        )

        resp = submit_task(req, fabric, ctx)

        assert isinstance(resp.escalation_reasons, list), (
            f"escalation_reasons must be a list, got {type(resp.escalation_reasons).__name__}"
        )
        assert not callable(resp.escalation_reasons), (
            "escalation_reasons must not be callable (function leaked into response)"
        )

    def test_submit_task_does_not_raise_when_escalation_metadata_is_built(self):
        """submit_task() must not throw TypeError when building the
        SpineResponse with escalation metadata."""
        from torment_service.spine import submit_task, SpineRequest

        fabric = _make_mock_fabric()
        ctx = _make_ctx()
        req = SpineRequest(
            workspace_id="ws_test",
            agent_id="ag_test",
            operation="ingest",
            payload={"text": "test memory", "step": 2},
        )

        # Should not raise TypeError: 'function' object is not iterable
        try:
            resp = submit_task(req, fabric, ctx)
        except TypeError as e:
            if "not iterable" in str(e):
                raise AssertionError(
                    f"submit_task raised TypeError on escalation assembly: {e}"
                ) from e
            raise

        assert resp.ok, f"Expected ok=True, got ok={resp.ok}, reason={resp.reason}"

    def test_escalation_reasons_is_list_when_escalated(self):
        """When escalation fires, escalation_reasons must still be a
        concrete list of strings."""
        from torment_service.spine import submit_task, SpineRequest
        from unittest.mock import patch

        fabric = _make_mock_fabric()
        ctx = _make_ctx()

        req = SpineRequest(
            workspace_id="ws_test",
            agent_id="ag_test",
            operation="ingest",
            payload={"text": "identity sensitive input", "step": 3},
            mode="auto",
        )

        def fake_escalation_reasons(*args, **kwargs):
            return ["test_escalation_trigger"]

        with patch("torment_service.spine.escalation_reasons",
                    side_effect=fake_escalation_reasons), \
             patch("torment_service.spine.should_escalate",
                    return_value=True):
            resp = submit_task(req, fabric, ctx)

        assert isinstance(resp.escalation_reasons, list), (
            f"escalation_reasons must be a list even when escalated, "
            f"got {type(resp.escalation_reasons).__name__}"
        )
        # When escalation fired, reasons should be non-empty
        if resp.escalated:
            assert len(resp.escalation_reasons) > 0, (
                "escalation_reasons should be non-empty when escalated=True"
            )
            for r in resp.escalation_reasons:
                assert isinstance(r, str), (
                    f"each escalation reason should be a string, got {type(r).__name__}"
                )

    def test_escalation_reasons_serializable(self):
        """The SpineResponse.to_dict() must not fail on escalation_reasons."""
        from torment_service.spine import submit_task, SpineRequest
        import json

        fabric = _make_mock_fabric()
        ctx = _make_ctx()
        req = SpineRequest(
            workspace_id="ws_test",
            agent_id="ag_test",
            operation="ingest",
            payload={"text": "serialize test", "step": 4},
        )

        resp = submit_task(req, fabric, ctx)
        d = resp.to_dict()

        assert "escalation_reasons" in d, "to_dict() must include escalation_reasons"
        assert isinstance(d["escalation_reasons"], list), (
            f"serialized escalation_reasons must be a list, "
            f"got {type(d['escalation_reasons']).__name__}"
        )
        # Must be JSON-serializable
        try:
            json.dumps(d["escalation_reasons"])
        except (TypeError, ValueError) as e:
            raise AssertionError(
                f"escalation_reasons must be JSON-serializable: {e}"
            ) from e


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_escalation_reasons_tests():
    tests = [
        ("ESC.1 escalation_reasons is list, not callable",
         TestEscalationReasonsIsList().test_submit_task_escalation_reasons_is_list_not_callable),
        ("ESC.2 submit_task does not raise TypeError on escalation assembly",
         TestEscalationReasonsIsList().test_submit_task_does_not_raise_when_escalation_metadata_is_built),
        ("ESC.3 escalation_reasons is list when escalated",
         TestEscalationReasonsIsList().test_escalation_reasons_is_list_when_escalated),
        ("ESC.4 escalation_reasons is JSON-serializable",
         TestEscalationReasonsIsList().test_escalation_reasons_serializable),
    ]

    passed = 0
    failed = 0
    print("\n--- Spine Escalation Reasons Tests ---")
    for name, fn in tests:
        try:
            fn()
            print(f"  PASS: {name}")
            passed += 1
        except Exception:
            print(f"  FAIL: {name}")
            traceback.print_exc()
            failed += 1

    return passed, failed


if __name__ == "__main__":
    p, f = run_escalation_reasons_tests()
    print(f"\nSpine Escalation Reasons: {p} passed, {f} failed")
    if f > 0:
        exit(1)
