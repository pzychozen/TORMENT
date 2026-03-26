# cognition/drift.py
"""
Drift Check — wraps character.py's measure_drift() for the cognition layer.

This module provides a clean interface between the Agent Spine and the
existing character drift measurement system. In v0.1 this is a lightweight
adapter; future versions may add caching, thresholds, or composite scoring.

The cognition layer calls `check_drift(workspace_id, agent_id)` and gets
back a DriftReport. Under the hood, this wraps character.measure_drift()
from torment_service.

When running without a live fabric instance (tests, dry runs), use
`stub_drift_check()` which returns a configurable DriftReport without
touching the fabric layer.

See AGENT_SPINE_PLAN.md §15.3 for drift threshold policy.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from schemas.drift_report import DriftReport, DRIFT_GREEN, DRIFT_YELLOW, DRIFT_RED


# ============================================================================
# Stub / test drift check
# ============================================================================

def stub_drift_check(
    total_drift: float = 0.0,
    domain_shift: float = 0.0,
    motif_shift: float = 0.0,
    style_shift: float = 0.0,
    governance_breach: bool = False,
    reasons: Optional[list] = None,
) -> "DriftCheckFn":
    """Create a drift check function that always returns the given DriftReport.

    Useful for testing the cognition pipeline without a live fabric instance.

    Usage:
        drift_fn = stub_drift_check(total_drift=0.25)
        result = reintegrate(task, routing, outputs, ctx, drift_check_fn=drift_fn)

    Returns a callable with signature (workspace_id, agent_id) -> DriftReport.
    """
    report = DriftReport(
        total_drift=total_drift,
        domain_shift=domain_shift,
        motif_shift=motif_shift,
        style_shift=style_shift,
        governance_breach=governance_breach,
        reasons=reasons or [],
    )

    def _check(workspace_id: str, agent_id: str) -> DriftReport:
        return report

    return _check


def zero_drift_check() -> "DriftCheckFn":
    """Convenience: drift check that always returns green/zero drift."""
    return stub_drift_check(total_drift=0.0)


def failing_drift_check() -> "DriftCheckFn":
    """Convenience: drift check that always raises (tests error handling)."""
    def _check(workspace_id: str, agent_id: str) -> DriftReport:
        raise RuntimeError("Drift measurement service unavailable")
    return _check


# ============================================================================
# Live drift check adapter
# ============================================================================

def make_live_drift_check(fabric_instance) -> "DriftCheckFn":
    """Create a drift check function backed by a live TormentFabric instance.

    This wraps character.measure_drift() through the fabric's workspace/agent
    objects. It requires a running fabric with initialized workspaces.

    Parameters
    ----------
    fabric_instance : TormentFabric
        A live fabric instance with access to workspace graphs, motif registries,
        and character state.

    Returns
    -------
    DriftCheckFn
        A callable: (workspace_id, agent_id) -> DriftReport
    """
    def _check(workspace_id: str, agent_id: str) -> DriftReport:
        try:
            # Import here to avoid circular dependency at module load time
            from torment_service.character import measure_drift

            ws = fabric_instance.get_workspace(workspace_id)
            ident = fabric_instance.create_agent(workspace_id, agent_id)

            # Get required objects from workspace/agent
            graph = ident.graph
            motif_registry = ws.motif_registry
            coherence_field = getattr(ws, "coherence_field", None)
            seed = ident.character_seed
            current_step = getattr(ws, "step_counter", 0)
            previous_state = getattr(ident, "character_state", None)

            raw = measure_drift(
                graph=graph,
                motif_registry=motif_registry,
                coherence_field=coherence_field,
                seed=seed,
                agent_id=agent_id,
                current_step=current_step,
                previous_state=previous_state,
            )

            # Convert raw drift dict to DriftReport
            return _raw_to_drift_report(raw)

        except Exception as e:
            # Drift check failure → return hard_block as safety fallback
            return DriftReport(
                total_drift=DRIFT_RED,
                governance_breach=False,
                reasons=[f"Live drift check failed: {str(e)}"],
            )

    return _check


def _raw_to_drift_report(raw: Dict[str, Any]) -> DriftReport:
    """Convert the raw dict from character.measure_drift() to a DriftReport.

    character.measure_drift() returns a dict with keys like:
      drift_score, domain_drift, motif_drift, style_drift, etc.
    We map these to our DriftReport fields.
    """
    return DriftReport(
        total_drift=raw.get("drift_score", raw.get("total_drift", 0.0)),
        domain_shift=raw.get("domain_drift", raw.get("domain_shift", 0.0)),
        motif_shift=raw.get("motif_drift", raw.get("motif_shift", 0.0)),
        style_shift=raw.get("style_drift", raw.get("style_shift", 0.0)),
        governance_breach=raw.get("governance_breach", False),
        reasons=raw.get("reasons", raw.get("drift_reasons", [])),
    )


# Type alias for documentation
DriftCheckFn = Callable[[str, str], DriftReport]
