# schemas/memory_proposal.py
"""
MemoryProposal — structured durable-write proposal from the archivist.

Invariant A: only the archivist path may propose durable memory writes.
Invariant G: low-trust derived material cannot overwrite high-trust source memory.

See AGENT_SPINE_PLAN.md §5.5 for the contract definition.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Optional

from .provenance import Provenance


# Default governance flags — all conservative (no special permissions)
DEFAULT_GOVERNANCE_FLAGS: Dict[str, bool] = {
    "protected": False,
    "non_shareable": False,
    "decay_accelerated": False,
    "collective_export_blocked": False,
    "eligible_for_collective_review": False,   # future hook, not acted on in v0.1
}


@dataclass
class MemoryProposal:
    """A structured proposal for a durable memory write, produced by the archivist."""

    proposal_id: str                            # UUID, auto-generated
    summary: str                                # human-readable summary of what to store
    content: str                                # full content to be ingested
    target_domain: str                          # which domain this memory targets
    proposed_strength: float                    # 0.0 - 1.0
    half_life_days: float                       # consistent with ShareProposal convention
    memory_type: str                            # "episode" | "insight" | "motif_seed"
    governance_flags: Dict[str, bool] = field(default_factory=lambda: dict(DEFAULT_GOVERNANCE_FLAGS))
    provenance: Optional[Provenance] = None     # mandatory in practice; Optional for deserialization safety

    # Archivist decision fields (filled during review)
    decision: str = "pending"                   # "pending" | "approved" | "rejected"
    rejection_reason: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.proposal_id:
            self.proposal_id = str(uuid.uuid4())
        if not (0.0 <= self.proposed_strength <= 1.0):
            raise ValueError(f"proposed_strength must be in [0.0, 1.0], got {self.proposed_strength}")
        if self.half_life_days <= 0:
            raise ValueError(f"half_life_days must be > 0, got {self.half_life_days}")

    def approve(self) -> None:
        self.decision = "approved"
        self.rejection_reason = None

    def reject(self, reason: str) -> None:
        self.decision = "rejected"
        self.rejection_reason = reason

    @property
    def is_approved(self) -> bool:
        return self.decision == "approved"

    @property
    def is_rejected(self) -> bool:
        return self.decision == "rejected"

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "MemoryProposal":
        if not d:
            raise ValueError("Cannot create MemoryProposal from empty dict")
        d = dict(d)
        # Reconstitute nested Provenance
        if "provenance" in d and isinstance(d["provenance"], dict):
            d["provenance"] = Provenance.from_dict(d["provenance"])
        known = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in d.items() if k in known}
        return cls(**filtered)

    @classmethod
    def create(
        cls,
        summary: str,
        content: str,
        target_domain: str,
        proposed_strength: float,
        half_life_days: float,
        memory_type: str,
        provenance: Provenance,
        governance_flags: Optional[Dict[str, bool]] = None,
    ) -> "MemoryProposal":
        """Convenience factory with auto-generated proposal_id."""
        return cls(
            proposal_id=str(uuid.uuid4()),
            summary=summary,
            content=content,
            target_domain=target_domain,
            proposed_strength=proposed_strength,
            half_life_days=half_life_days,
            memory_type=memory_type,
            governance_flags=governance_flags or dict(DEFAULT_GOVERNANCE_FLAGS),
            provenance=provenance,
        )
