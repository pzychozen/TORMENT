"""
v0.1.0a test: TormentFabric's drift check fires the registered
drift_reflex_callback on a below→above high-regime transition, and
does NOT re-fire while drift stays high or under other conditions.

Tests exercise the callback-registration and transition-firing logic
via a minimal fabric harness that simulates the internal state
machine added at fabric.py:~2939-3050. This keeps the test isolated
from the full TormentFabric initialization (which needs data_dir +
embedder + etc.) while proving the exact contract the v0.1.0a
increment adds:

    - callback fires exactly once on transition from below to above
    - callback does NOT fire when drift stays above (no re-spam)
    - callback does NOT fire when drift is high but direction != away_seed
    - callback does NOT fire when drift is low
    - callback does NOT fire when it's None (default state)
    - a drift drop-then-rise re-arms the transition (second fire OK)
    - callback exceptions do not propagate out of the drift check

References:
    - docs/TORMENT_AGENT_DOCTRINE_v0.1.md Part 4 (high regime)
    - docs/TORMENT_AGENT_RUNTIME_SLICE_v0.1_PLAN.md v0.1.0a
    - torment_service/fabric.py (drift check block after gravity_correction)
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Harness — mirrors the exact state-machine shape fabric.py uses
# ---------------------------------------------------------------------------


@dataclass
class FabricDriftHarness:
    """Isolated re-implementation of fabric.py's v0.1.0a drift-reflex
    transition logic. The real code at fabric.py:~2990-3050 runs
    inside a larger ingest pipeline; this harness extracts just the
    reflex-firing contract for testing.

    If this harness diverges from fabric.py's actual behavior, the
    test becomes misleading. Any change to the fabric drift check
    MUST be mirrored here (and vice versa). The harness is the
    single-source-of-truth contract.
    """
    drift_reflex_callback: Optional[Any] = None  # (ws, agent, drift) -> None
    _last_drift_was_high: Dict[Tuple[str, str], bool] = field(default_factory=dict)
    drift_correction_threshold: float = 0.35

    # Instrumentation so tests can inspect what happened
    callback_exceptions_caught: int = 0

    def simulate_drift_check(
        self,
        workspace_id: str,
        agent_id: str,
        drift: Dict[str, Any],
    ) -> None:
        """Mirror of fabric.py's drift-check transition logic."""
        _is_high_drift = (
            float(drift["drift_score"]) < -self.drift_correction_threshold
            and str(drift["drift_direction"]) == "away_seed"
        )

        _reflex_key = (workspace_id, agent_id)
        _was_high = self._last_drift_was_high.get(_reflex_key, False)
        self._last_drift_was_high[_reflex_key] = _is_high_drift

        if (
            _is_high_drift
            and not _was_high
            and self.drift_reflex_callback is not None
        ):
            try:
                self.drift_reflex_callback(workspace_id, agent_id, dict(drift))
            except Exception:
                self.callback_exceptions_caught += 1
                # Real fabric.py logs + continues; here we just record it


@dataclass
class RecordingCallback:
    """Test double for the drift-reflex callback."""
    calls: List[Dict[str, Any]] = field(default_factory=list)
    raise_on_call: bool = False

    def __call__(self, workspace_id, agent_id, drift_info):
        call = {
            "workspace_id": workspace_id,
            "agent_id": agent_id,
            "drift_info": drift_info,
        }
        self.calls.append(call)
        if self.raise_on_call:
            raise RuntimeError("simulated callback failure")


# Common drift dicts (using corrected sign convention: negative = far)
HIGH_AWAY = {"drift_score": -0.5, "drift_direction": "away_seed"}
HIGH_TOWARD = {"drift_score": -0.5, "drift_direction": "toward_seed"}
LOW_AWAY = {"drift_score": -0.05, "drift_direction": "away_seed"}
CENTERED = {"drift_score": 0.3, "drift_direction": "stable"}


# ---------------------------------------------------------------------------
# Transition firing
# ---------------------------------------------------------------------------


class TestCallbackFiresOnTransition:
    """Callback fires exactly once when drift crosses below→above."""

    def test_fires_on_first_high_reading(self):
        cb = RecordingCallback()
        h = FabricDriftHarness(drift_reflex_callback=cb)
        h.simulate_drift_check("ws", "agent", HIGH_AWAY)
        assert len(cb.calls) == 1
        assert cb.calls[0]["workspace_id"] == "ws"
        assert cb.calls[0]["agent_id"] == "agent"
        assert cb.calls[0]["drift_info"]["drift_score"] == -0.5

    def test_callback_receives_drift_info_copy(self):
        """Harness passes a dict copy, not the original."""
        cb = RecordingCallback()
        h = FabricDriftHarness(drift_reflex_callback=cb)
        h.simulate_drift_check("ws", "agent", HIGH_AWAY)
        # Mutating the argument post-call must not affect the recorded dict
        HIGH_AWAY["drift_score"] = -0.99  # paranoid test; we'll revert
        assert cb.calls[0]["drift_info"]["drift_score"] == -0.5
        HIGH_AWAY["drift_score"] = -0.5  # revert


# ---------------------------------------------------------------------------
# No re-fire while drift stays high
# ---------------------------------------------------------------------------


class TestNoReFireWhileHigh:
    """Once in the high regime, subsequent high readings DO NOT re-fire."""

    def test_two_consecutive_high_readings_one_fire(self):
        cb = RecordingCallback()
        h = FabricDriftHarness(drift_reflex_callback=cb)
        h.simulate_drift_check("ws", "agent", HIGH_AWAY)
        h.simulate_drift_check("ws", "agent", HIGH_AWAY)
        assert len(cb.calls) == 1

    def test_many_consecutive_high_readings_one_fire(self):
        cb = RecordingCallback()
        h = FabricDriftHarness(drift_reflex_callback=cb)
        for _ in range(10):
            h.simulate_drift_check("ws", "agent", HIGH_AWAY)
        assert len(cb.calls) == 1


# ---------------------------------------------------------------------------
# Drop and rise re-arms the transition (second fire OK)
# ---------------------------------------------------------------------------


class TestDropAndRiseReArms:
    """A drift drop below threshold resets the state; a subsequent
    rise back above threshold fires the callback again."""

    def test_high_then_low_then_high_fires_twice(self):
        cb = RecordingCallback()
        h = FabricDriftHarness(drift_reflex_callback=cb)
        h.simulate_drift_check("ws", "agent", HIGH_AWAY)   # fire 1
        h.simulate_drift_check("ws", "agent", LOW_AWAY)    # no fire; resets
        h.simulate_drift_check("ws", "agent", HIGH_AWAY)   # fire 2
        assert len(cb.calls) == 2

    def test_high_then_centered_then_high_fires_twice(self):
        cb = RecordingCallback()
        h = FabricDriftHarness(drift_reflex_callback=cb)
        h.simulate_drift_check("ws", "agent", HIGH_AWAY)
        h.simulate_drift_check("ws", "agent", CENTERED)
        h.simulate_drift_check("ws", "agent", HIGH_AWAY)
        assert len(cb.calls) == 2


# ---------------------------------------------------------------------------
# Non-firing conditions
# ---------------------------------------------------------------------------


class TestDoesNotFireInvalidStates:
    """Callback should NOT fire under these conditions."""

    def test_high_but_toward_seed_no_fire(self):
        """Direction matters — high magnitude toward_seed does NOT fire."""
        cb = RecordingCallback()
        h = FabricDriftHarness(drift_reflex_callback=cb)
        h.simulate_drift_check("ws", "agent", HIGH_TOWARD)
        assert len(cb.calls) == 0

    def test_low_drift_no_fire(self):
        cb = RecordingCallback()
        h = FabricDriftHarness(drift_reflex_callback=cb)
        h.simulate_drift_check("ws", "agent", LOW_AWAY)
        assert len(cb.calls) == 0

    def test_centered_no_fire(self):
        cb = RecordingCallback()
        h = FabricDriftHarness(drift_reflex_callback=cb)
        h.simulate_drift_check("ws", "agent", CENTERED)
        assert len(cb.calls) == 0

    def test_no_callback_no_fire(self):
        """Default state: callback is None, drift check runs normally."""
        h = FabricDriftHarness(drift_reflex_callback=None)
        # Should not raise
        h.simulate_drift_check("ws", "agent", HIGH_AWAY)
        h.simulate_drift_check("ws", "agent", HIGH_AWAY)
        # State is still updated even without a callback
        assert h._last_drift_was_high[("ws", "agent")] is True

    def test_positive_drift_score_no_fire(self):
        """Positive drift_score is centered/healthy by convention;
        never high regardless of magnitude or direction."""
        cb = RecordingCallback()
        h = FabricDriftHarness(drift_reflex_callback=cb)
        positive_state = {"drift_score": 0.8, "drift_direction": "away_seed"}
        h.simulate_drift_check("ws", "agent", positive_state)
        assert len(cb.calls) == 0


# ---------------------------------------------------------------------------
# Per-agent state isolation
# ---------------------------------------------------------------------------


class TestPerAgentStateIsolation:
    """_last_drift_was_high is keyed per (workspace, agent); two
    agents in the same workspace don't share transition state."""

    def test_two_agents_independent_transitions(self):
        cb = RecordingCallback()
        h = FabricDriftHarness(drift_reflex_callback=cb)
        # Agent A: high → should fire
        h.simulate_drift_check("ws", "agent_a", HIGH_AWAY)
        # Agent B: high for the first time → should also fire
        h.simulate_drift_check("ws", "agent_b", HIGH_AWAY)
        assert len(cb.calls) == 2
        assert cb.calls[0]["agent_id"] == "agent_a"
        assert cb.calls[1]["agent_id"] == "agent_b"

    def test_two_workspaces_independent_transitions(self):
        cb = RecordingCallback()
        h = FabricDriftHarness(drift_reflex_callback=cb)
        h.simulate_drift_check("ws1", "agent", HIGH_AWAY)
        h.simulate_drift_check("ws2", "agent", HIGH_AWAY)
        assert len(cb.calls) == 2


# ---------------------------------------------------------------------------
# Callback exception handling
# ---------------------------------------------------------------------------


class TestCallbackExceptionsDoNotPropagate:
    """A raising callback must not break the drift check; fabric logs
    and continues."""

    def test_raising_callback_does_not_propagate(self):
        cb = RecordingCallback(raise_on_call=True)
        h = FabricDriftHarness(drift_reflex_callback=cb)
        # Should not raise
        h.simulate_drift_check("ws", "agent", HIGH_AWAY)
        # Exception was caught by harness (mirrors fabric.py's try/except)
        assert h.callback_exceptions_caught == 1
        # State is still updated (so subsequent checks use correct baseline)
        assert h._last_drift_was_high[("ws", "agent")] is True

    def test_raising_callback_state_still_advances(self):
        """Even if the callback raises, the transition state updates so
        we don't spin trying to re-fire."""
        cb = RecordingCallback(raise_on_call=True)
        h = FabricDriftHarness(drift_reflex_callback=cb)
        h.simulate_drift_check("ws", "agent", HIGH_AWAY)
        h.simulate_drift_check("ws", "agent", HIGH_AWAY)
        # Only one call attempt (first was the transition; second is same-state)
        assert len(cb.calls) == 1
        assert h.callback_exceptions_caught == 1


# ---------------------------------------------------------------------------
# Recursion contract (the reason for transition-only firing)
# ---------------------------------------------------------------------------


class TestRecursionContract:
    """Simulates the recursion risk: a reflex callback that would
    trigger another ingest. Transition-only firing prevents infinite
    recursion."""

    def test_callback_triggers_nested_drift_check_no_refire(self):
        """If the callback causes another drift check (simulating the
        reflex turn's ingest), the nested check should NOT re-fire
        the callback because state is already 'high'."""
        cb = RecordingCallback()
        h = FabricDriftHarness(drift_reflex_callback=cb)

        # Simulate: reflex callback causes another drift check
        def nested_callback(ws, agent, drift):
            # This is what the reflex's own ingest would look like
            h.simulate_drift_check(ws, agent, HIGH_AWAY)
            cb.calls.append({"workspace_id": ws, "agent_id": agent, "drift_info": drift})

        h.drift_reflex_callback = nested_callback
        h.simulate_drift_check("ws", "agent", HIGH_AWAY)

        # Only one call — the nested simulate_drift_check saw state
        # was already high and did not re-fire.
        assert len(cb.calls) == 1
