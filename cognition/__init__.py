# cognition — governed cognition pipeline for TORMENT Agent Spine (v0.1)
#
# This package implements a single-pass pipeline:
#   TaskPacket → Router → Apertures → Roles → Reintegration → Archivist → Response
#
# It sits ABOVE the existing memory layer and does not replace it.
# See docs/archive/AGENT_SPINE_PLAN.md for the full design rationale.

from .task_models import TaskPacket, RoutingDecision, ReintegrationResult
from .router import detect_mode, route
from .apertures import (
    ApertureConfig,
    MemoryContext,
    APERTURE_CONFIGS,
    get_config,
    build_memory_context,
)
from .reintegration import reintegrate
from .drift import (
    stub_drift_check,
    zero_drift_check,
    failing_drift_check,
    make_live_drift_check,
)
from .pipeline import run_cognition_pipeline

__all__ = [
    "TaskPacket",
    "RoutingDecision",
    "ReintegrationResult",
    "detect_mode",
    "route",
    "ApertureConfig",
    "MemoryContext",
    "APERTURE_CONFIGS",
    "get_config",
    "build_memory_context",
    "reintegrate",
    "stub_drift_check",
    "zero_drift_check",
    "failing_drift_check",
    "make_live_drift_check",
    "run_cognition_pipeline",
]
