# schemas/provenance.py
"""
Provenance — mandatory lineage metadata for every role output and memory proposal.

Invariant B from the Agent Spine plan: provenance is mandatory and must be
a structured object, never a string blob.

See AGENT_SPINE_PLAN.md §5.3 for the contract definition.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


# Valid source types — kept as constants so tests can reference them.
SOURCE_USER_INPUT = "user_input"
SOURCE_ROLE_OUTPUT = "role_output"
SOURCE_DERIVED = "derived"
SOURCE_MEMORY = "memory"
VALID_SOURCE_TYPES = frozenset({
    SOURCE_USER_INPUT,
    SOURCE_ROLE_OUTPUT,
    SOURCE_DERIVED,
    SOURCE_MEMORY,
})

# Valid verification statuses
STATUS_UNVERIFIED = "unverified"
STATUS_SKEPTIC_PASSED = "skeptic_passed"
STATUS_SKEPTIC_FLAGGED = "skeptic_flagged"
VALID_VERIFICATION_STATUSES = frozenset({
    STATUS_UNVERIFIED,
    STATUS_SKEPTIC_PASSED,
    STATUS_SKEPTIC_FLAGGED,
})


@dataclass
class Provenance:
    """Structured lineage for any piece of data flowing through the spine."""

    source_type: str                    # one of VALID_SOURCE_TYPES
    source_role: Optional[str] = None   # which role produced this (None for user input)
    parent_ids: List[str] = field(default_factory=list)  # task_id or prior provenance chain
    derivation_depth: int = 0           # 0 = direct from user, 1+ = derived
    confidence: float = 1.0             # 0.0 - 1.0
    verification_status: str = STATUS_UNVERIFIED
    timestamp: int = 0                  # unix epoch; auto-filled if 0

    def __post_init__(self) -> None:
        if self.source_type not in VALID_SOURCE_TYPES:
            raise ValueError(
                f"Invalid source_type '{self.source_type}'. "
                f"Must be one of: {sorted(VALID_SOURCE_TYPES)}"
            )
        if self.verification_status not in VALID_VERIFICATION_STATUSES:
            raise ValueError(
                f"Invalid verification_status '{self.verification_status}'. "
                f"Must be one of: {sorted(VALID_VERIFICATION_STATUSES)}"
            )
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(f"confidence must be in [0.0, 1.0], got {self.confidence}")
        if self.derivation_depth < 0:
            raise ValueError(f"derivation_depth must be >= 0, got {self.derivation_depth}")
        if self.timestamp == 0:
            self.timestamp = int(time.time())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Provenance":
        if not d:
            raise ValueError("Cannot create Provenance from empty dict")
        known = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in d.items() if k in known}
        return cls(**filtered)

    def derive(self, role_name: str, confidence: float = 1.0) -> "Provenance":
        """Create a child provenance from this one (increments derivation depth)."""
        return Provenance(
            source_type=SOURCE_DERIVED,
            source_role=role_name,
            parent_ids=self.parent_ids + ([str(self.timestamp)]),
            derivation_depth=self.derivation_depth + 1,
            confidence=min(self.confidence, confidence),
            verification_status=STATUS_UNVERIFIED,
        )

    @classmethod
    def from_user(cls, task_id: str) -> "Provenance":
        """Create root provenance for direct user input."""
        return cls(
            source_type=SOURCE_USER_INPUT,
            source_role=None,
            parent_ids=[task_id],
            derivation_depth=0,
            confidence=1.0,
            verification_status=STATUS_UNVERIFIED,
        )

    @classmethod
    def from_role(cls, role_name: str, task_id: str, confidence: float = 1.0) -> "Provenance":
        """Create provenance for a role's direct output."""
        return cls(
            source_type=SOURCE_ROLE_OUTPUT,
            source_role=role_name,
            parent_ids=[task_id],
            derivation_depth=1,
            confidence=confidence,
            verification_status=STATUS_UNVERIFIED,
        )
