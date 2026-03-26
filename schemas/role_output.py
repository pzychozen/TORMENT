# schemas/role_output.py
"""
RoleOutput — structured output from any cognition role.

Each role (interpreter, engineer, skeptic, archivist) produces one of these.
The reintegration membrane merges them, preserving contradictions (Invariant C).

See AGENT_SPINE_PLAN.md §5.4 for the contract definition.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

from .provenance import Provenance
from .memory_proposal import MemoryProposal


@dataclass
class RoleOutput:
    """Structured output from a single role execution."""

    role_name: str
    summary: str                                    # one-line summary of what the role concluded
    findings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    uncertainties: List[str] = field(default_factory=list)
    contradictions: List[str] = field(default_factory=list)
    memory_proposals: List[MemoryProposal] = field(default_factory=list)
    confidence: float = 1.0                         # 0.0 - 1.0
    provenance: Optional[Provenance] = None

    def __post_init__(self) -> None:
        if not self.role_name:
            raise ValueError("role_name must not be empty")
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(f"confidence must be in [0.0, 1.0], got {self.confidence}")

    @property
    def has_contradictions(self) -> bool:
        return len(self.contradictions) > 0

    @property
    def has_memory_proposals(self) -> bool:
        return len(self.memory_proposals) > 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "RoleOutput":
        if not d:
            raise ValueError("Cannot create RoleOutput from empty dict")
        d = dict(d)
        # Reconstitute nested objects
        if "provenance" in d and isinstance(d["provenance"], dict):
            d["provenance"] = Provenance.from_dict(d["provenance"])
        if "memory_proposals" in d and isinstance(d["memory_proposals"], list):
            d["memory_proposals"] = [
                MemoryProposal.from_dict(mp) if isinstance(mp, dict) else mp
                for mp in d["memory_proposals"]
            ]
        known = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in d.items() if k in known}
        return cls(**filtered)
