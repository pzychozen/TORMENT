"""Regression tests for Spine drift enforcement alignment.

Verifies that _full_cognition() passes a live drift_check_fn into
run_cognition_pipeline(), closing the gap documented in
docs/ISSUE_spine_drift_check_fn_gap.md.
"""
import os
import sys
import traceback
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestSpineFullCognitionPassesDriftCheckFn:
    """Spy on run_cognition_pipeline() to verify _full_cognition wires
    drift_check_fn correctly."""

    def _make_stub_fabric(self):
        """Build a minimal mock fabric that _full_cognition can call."""
        fabric = MagicMock()
        # get_workspace returns an object with shared_graphs
        ws = MagicMock()
        ws.shared_graphs = {"default": MagicMock()}
        fabric.get_workspace.return_value = ws
        # character_store.load_state returns None (no character)
        fabric.character_store.load_state.return_value = None
        return fabric

    def _make_stub_request(self):
        """Build a minimal SpineRequest-like object."""
        from torment_service.spine import SpineRequest
        return SpineRequest(
            workspace_id="ws_test",
            agent_id="ag_test",
            operation="cognition_run",
            payload={"text": "Who am I?"},
        )

    def _make_stub_context(self):
        """Build a minimal RequestContext-like object."""
        from torment_service.request_context import RequestContext
        return RequestContext(
            client_id="test_client",
            trust_tier=1.0,
            workspace_id="ws_test",
            agent_id="ag_test",
        )

    def test_spine_full_cognition_passes_live_drift_check_fn(self):
        """_full_cognition must pass a non-None drift_check_fn to
        run_cognition_pipeline."""
        fabric = self._make_stub_fabric()
        req = self._make_stub_request()
        ctx = self._make_stub_context()

        # Spy on run_cognition_pipeline — intercept the call and return
        # a minimal valid result instead of actually running cognition.
        fake_result = {
            "ok": True,
            "task_id": "tsk_test",
            "final_answer": "test",
            "merged_findings": [],
            "dissent": [],
            "memory_effects": {},
            "drift_report": None,
            "governance_rejections": [],
            "role_summaries": [],
            "routing": {},
        }

        with patch("cognition.pipeline.run_cognition_pipeline",
                    return_value=fake_result) as spy:
            from torment_service.spine import _full_cognition
            _full_cognition(fabric, ctx, req)

            spy.assert_called_once()
            call_kwargs = spy.call_args
            # drift_check_fn may be positional or keyword — check both
            if call_kwargs.kwargs and "drift_check_fn" in call_kwargs.kwargs:
                dcf = call_kwargs.kwargs["drift_check_fn"]
            else:
                # Shouldn't happen with current code, but handle gracefully
                dcf = None
                for arg in (call_kwargs.args or []):
                    if callable(arg):
                        dcf = arg
                        break

            assert dcf is not None, (
                "_full_cognition must pass a non-None drift_check_fn "
                "to run_cognition_pipeline (Invariant E enforcement)"
            )
            assert callable(dcf), (
                f"drift_check_fn must be callable, got {type(dcf)}"
            )

    def test_spine_drift_check_fn_is_from_make_live_drift_check(self):
        """The drift_check_fn passed by _full_cognition should be produced
        by make_live_drift_check (structural confirmation)."""
        import inspect
        from torment_service import spine as spine_mod
        source = inspect.getsource(spine_mod._full_cognition)

        assert "make_live_drift_check" in source, (
            "_full_cognition should import and use make_live_drift_check"
        )
        assert "drift_check_fn" in source, (
            "_full_cognition should pass drift_check_fn to the pipeline"
        )


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_spine_drift_tests():
    """Run all Spine drift enforcement tests."""
    tests = [
        ("SDR.1 _full_cognition passes non-None drift_check_fn",
         TestSpineFullCognitionPassesDriftCheckFn()
         .test_spine_full_cognition_passes_live_drift_check_fn),
        ("SDR.2 drift_check_fn is from make_live_drift_check (structural)",
         TestSpineFullCognitionPassesDriftCheckFn()
         .test_spine_drift_check_fn_is_from_make_live_drift_check),
    ]

    passed = 0
    failed = 0
    print("\n--- Spine Drift Enforcement Tests ---")
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
    p, f = run_spine_drift_tests()
    print(f"\nSpine Drift Enforcement: {p} passed, {f} failed")
    if f > 0:
        sys.exit(1)
