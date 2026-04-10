# schemas — frozen data contracts for the TORMENT Agent Spine (v0.1)
#
# These dataclasses define the communication protocol between cognition
# components.  They are intentionally simple and serializable.
#
# See docs/archive/AGENT_SPINE_PLAN.md §5 for the design rationale.

from .provenance import Provenance
from .drift_report import DriftReport
from .role_output import RoleOutput
from .memory_proposal import MemoryProposal

__all__ = [
    "Provenance",
    "DriftReport",
    "RoleOutput",
    "MemoryProposal",
]
