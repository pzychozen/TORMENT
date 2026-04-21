# tests/test_session_lifecycle_hook_presence.py
"""
T6 — Presence test for the SessionLifecycleHook Protocol.

Covers BLOCK_A_DESIGN.md §9:

    Block A declares a SessionLifecycleHook Protocol in agent_loop.py
    but does NOT wire it into AgentRunner. Implementation is deferred
    to a post-slice runtime increment.

This test asserts that:
    1. The Protocol class exists.
    2. It declares on_session_start and on_session_end methods.
    3. It is NOT wired to AgentRunner (constructor has no hook param).

There is no behavior test. The Protocol has no behavior in Block A —
it is a reserved interface, nothing more. See BLOCK_A_IMPLEMENTATION_
ANALYSIS.md §3.4 for deferral rationale and BLOCK_A_DESIGN.md §9 for
the declaration-only scope.

This test FAILS against current code (pre-implementation) — the
Protocol does not yet exist. Passes once `SessionLifecycleHook` is
added to torment_service/agent_loop.py per §9.
"""
from __future__ import annotations

import inspect
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestSessionLifecycleHookDeclared(unittest.TestCase):
    """The Protocol class must exist with the declared method shape."""

    def test_hook_class_importable(self) -> None:
        try:
            from torment_service.agent_loop import SessionLifecycleHook
        except ImportError as e:
            self.fail(f"SessionLifecycleHook must be importable from "
                      f"torment_service.agent_loop per §9: {e}")

    def test_hook_declares_on_session_start(self) -> None:
        from torment_service.agent_loop import SessionLifecycleHook
        self.assertTrue(
            hasattr(SessionLifecycleHook, "on_session_start"),
            "SessionLifecycleHook must declare on_session_start per §9"
        )

    def test_hook_declares_on_session_end(self) -> None:
        from torment_service.agent_loop import SessionLifecycleHook
        self.assertTrue(
            hasattr(SessionLifecycleHook, "on_session_end"),
            "SessionLifecycleHook must declare on_session_end per §9"
        )

    def test_on_session_start_signature(self) -> None:
        from torment_service.agent_loop import SessionLifecycleHook
        sig = inspect.signature(SessionLifecycleHook.on_session_start)
        params = list(sig.parameters.keys())
        # self + workspace_id + agent_id + session_id
        for required in ("workspace_id", "agent_id", "session_id"):
            self.assertIn(
                required, params,
                f"on_session_start must accept {required} per §9 signature"
            )

    def test_on_session_end_signature(self) -> None:
        from torment_service.agent_loop import SessionLifecycleHook
        sig = inspect.signature(SessionLifecycleHook.on_session_end)
        params = list(sig.parameters.keys())
        for required in ("workspace_id", "agent_id", "session_id"):
            self.assertIn(
                required, params,
                f"on_session_end must accept {required} per §9 signature"
            )


class TestHookNotWiredToAgentRunner(unittest.TestCase):
    """D.2 + §9: Protocol is declared only. AgentRunner must not accept
    a hook parameter in v0.1. Activation is a later runtime increment."""

    def test_agent_runner_constructor_has_no_hook_parameter(self) -> None:
        from torment_service.agent_loop import AgentRunner
        sig = inspect.signature(AgentRunner.__init__)
        param_names = set(sig.parameters.keys())
        for forbidden in (
            "session_hook", "lifecycle_hook",
            "session_lifecycle_hook", "hook",
            "on_session_start", "on_session_end",
        ):
            self.assertNotIn(
                forbidden, param_names,
                f"AgentRunner.__init__ must not accept {forbidden!r} — "
                "Block A declares SessionLifecycleHook but does not wire it"
            )


if __name__ == "__main__":
    unittest.main()
