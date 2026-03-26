# cognition/task_models.py
"""
Core data models for the TORMENT cognition pipeline.

TaskPacket     — incoming request context
RoutingDecision — router output: which roles, what aperture, what constraints
ReintegrationResult — merged output from the reintegration membrane

See AGENT_SPINE_PLAN.md §5 for contract definitions and §15 for resolved
design decisions.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

from schemas.drift_report import DriftReport
from schemas.memory_proposal import MemoryProposal
from schemas.role_output import RoleOutput


# ============================================================================
# TaskPacket
# ============================================================================

# Valid modes for task classification
MODE_AUTO = "auto"
MODE_ENGINEERING = "engineering"
MODE_STRATEGIC = "strategic"
MODE_IDENTITY = "identity"
VALID_MODES = frozenset({MODE_AUTO, MODE_ENGINEERING, MODE_STRATEGIC, MODE_IDENTITY})

# Valid priorities
PRIORITY_LOW = "low"
PRIORITY_NORMAL = "normal"
PRIORITY_HIGH = "high"
VALID_PRIORITIES = frozenset({PRIORITY_LOW, PRIORITY_NORMAL, PRIORITY_HIGH})


@dataclass
class TaskPacket:
    """Carries an incoming request through the cognition pipeline."""

    workspace_id: str
    agent_id: str
    user_input: str
    task_id: str = ""                   # auto-generated if empty
    mode: str = MODE_AUTO               # "auto" | "engineering" | "strategic" | "identity"
    priority: str = PRIORITY_NORMAL     # "low" | "normal" | "high"
    timestamp: int = 0                  # unix epoch, auto-filled if 0

    def __post_init__(self) -> None:
        if not self.task_id:
            self.task_id = f"tsk_{uuid.uuid4().hex[:12]}"
        if self.mode not in VALID_MODES:
            raise ValueError(
                f"Invalid mode '{self.mode}'. Must be one of: {sorted(VALID_MODES)}"
            )
        if self.priority not in VALID_PRIORITIES:
            raise ValueError(
                f"Invalid priority '{self.priority}'. Must be one of: {sorted(VALID_PRIORITIES)}"
            )
        if not self.workspace_id:
            raise ValueError("workspace_id must not be empty")
        if not self.agent_id:
            raise ValueError("agent_id must not be empty")
        if not self.user_input:
            raise ValueError("user_input must not be empty")
        if self.timestamp == 0:
            self.timestamp = int(time.time())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "TaskPacket":
        if not d:
            raise ValueError("Cannot create TaskPacket from empty dict")
        known = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in d.items() if k in known}
        return cls(**filtered)


# ============================================================================
# RoutingDecision
# ============================================================================

# Valid aperture types
APERTURE_NARROW = "narrow"
APERTURE_BROAD = "broad"
APERTURE_PROTECTED = "protected"
VALID_APERTURES = frozenset({APERTURE_NARROW, APERTURE_BROAD, APERTURE_PROTECTED})

# Valid archival scopes — max eligible destination for archivist-approved writes.
# Roles never write directly. (AGENT_SPINE_PLAN.md §15, tightening #1)
SCOPE_NONE = "none"
SCOPE_PRIVATE = "private"
VALID_ARCHIVAL_SCOPES = frozenset({SCOPE_NONE, SCOPE_PRIVATE})


@dataclass
class RoutingDecision:
    """Router output: determines role activation, aperture, and constraints."""

    roles_to_activate: List[str]            # e.g. ["interpreter", "engineer", "skeptic", "archivist"]
    primary_domains: List[str]              # from fabric domain routing
    aperture: str                           # "narrow" | "broad" | "protected"
    memory_sources: List[str] = field(default_factory=lambda: ["private", "shared"])
    archival_scope: str = SCOPE_PRIVATE     # "none" | "private"
    conflict_policy: str = "preserve"       # v0.1 only supports "preserve"
    require_skeptic_pass: bool = False
    require_drift_check: bool = False
    require_archival_review: bool = True    # always true in v0.1

    def __post_init__(self) -> None:
        if self.aperture not in VALID_APERTURES:
            raise ValueError(
                f"Invalid aperture '{self.aperture}'. "
                f"Must be one of: {sorted(VALID_APERTURES)}"
            )
        if self.archival_scope not in VALID_ARCHIVAL_SCOPES:
            raise ValueError(
                f"Invalid archival_scope '{self.archival_scope}'. "
                f"Must be one of: {sorted(VALID_ARCHIVAL_SCOPES)}"
            )
        if self.conflict_policy != "preserve":
            raise ValueError(
                f"v0.1 only supports conflict_policy='preserve', got '{self.conflict_policy}'"
            )
        if not self.roles_to_activate:
            raise ValueError("roles_to_activate must not be empty")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "RoutingDecision":
        if not d:
            raise ValueError("Cannot create RoutingDecision from empty dict")
        known = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in d.items() if k in known}
        return cls(**filtered)


# ============================================================================
# ReintegrationResult
# ============================================================================

@dataclass
class ReintegrationResult:
    """Output of the reintegration membrane.

    Invariant C: disagreement is preservable.  The `dissent` field holds
    structured contradictions that were NOT flattened during merge.
    """

    final_answer: str
    merged_findings: List[str] = field(default_factory=list)
    dissent: List[Dict[str, Any]] = field(default_factory=list)
    # Each dissent entry: {role_a, role_b, claim_a, claim_b, topic}
    role_outputs: List[RoleOutput] = field(default_factory=list)
    all_memory_proposals: List[MemoryProposal] = field(default_factory=list)
    governance_rejections: List[Dict[str, str]] = field(default_factory=list)
    # Each rejection: {proposal_id, reason}
    drift_report: Optional[DriftReport] = None
    memory_effects: Optional[Dict[str, List[Dict[str, Any]]]] = None
    # {"approved": [...], "rejected": [...]}

    @property
    def has_dissent(self) -> bool:
        return len(self.dissent) > 0

    @property
    def has_governance_rejections(self) -> bool:
        return len(self.governance_rejections) > 0

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if self.drift_report is not None:
            d["drift_report"] = self.drift_report.to_dict()
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ReintegrationResult":
        if not d:
            raise ValueError("Cannot create ReintegrationResult from empty dict")
        d = dict(d)
        if "drift_report" in d and isinstance(d["drift_report"], dict):
            d["drift_report"] = DriftReport.from_dict(d["drift_report"])
        if "role_outputs" in d and isinstance(d["role_outputs"], list):
            d["role_outputs"] = [
                RoleOutput.from_dict(ro) if isinstance(ro, dict) else ro
                for ro in d["role_outputs"]
            ]
        if "all_memory_proposals" in d and isinstance(d["all_memory_proposals"], list):
            d["all_memory_proposals"] = [
                MemoryProposal.from_dict(mp) if isinstance(mp, dict) else mp
                for mp in d["all_memory_proposals"]
            ]
        known = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in d.items() if k in known}
        return cls(**filtered)
