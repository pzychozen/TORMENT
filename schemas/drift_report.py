# schemas/drift_report.py
"""
DriftReport — structured output from the drift checker.

Used by the cognition layer to decide whether identity-sensitive durable
writes should proceed, be downgraded to provisional, or be blocked.

Drift threshold policy (from docs/archive/AGENT_SPINE_PLAN.md §15.3):
  < 0.20          green  — proceed normally
  0.20 – 0.35     yellow — provisional/private proposals only
  0.35 – 0.50     red    — explicit block + warning
  >= 0.50          hard block

See docs/archive/AGENT_SPINE_PLAN.md §5.6 for the contract definition.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List


# Drift policy thresholds
DRIFT_GREEN = 0.20
DRIFT_YELLOW = 0.35
DRIFT_RED = 0.50


@dataclass
class DriftReport:
    """Report produced by the drift checker for identity-sensitive flows."""

    total_drift: float = 0.0
    drift_direction: str = "stable"
    domain_shift: float = 0.0
    motif_shift: float = 0.0
    style_shift: float = 0.0
    governance_breach: bool = False
    reasons: List[str] = field(default_factory=list)

    @property
    def zone(self) -> str:
        """Return the policy zone: 'green', 'yellow', 'red', or 'hard_block'."""
        if self.total_drift < DRIFT_GREEN:
            return "green"
        elif self.total_drift < DRIFT_YELLOW:
            return "yellow"
        elif self.total_drift < DRIFT_RED:
            return "red"
        else:
            return "hard_block"

    @property
    def allows_durable_write(self) -> bool:
        """Whether a durable identity-sensitive write is permitted."""
        return self.zone == "green" and not self.governance_breach

    @property
    def allows_provisional_write(self) -> bool:
        """Whether a provisional (non-identity-shaping) write is permitted."""
        return self.zone in ("green", "yellow") and not self.governance_breach

    @property
    def requires_block(self) -> bool:
        """Whether all identity-sensitive durable writes must be blocked."""
        return (
            self.governance_breach
            or (
                self.zone in ("red", "hard_block")
                and self.drift_direction == "away_seed"
            )
        )

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["zone"] = self.zone
        d["allows_durable_write"] = self.allows_durable_write
        d["allows_provisional_write"] = self.allows_provisional_write
        d["requires_block"] = self.requires_block
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "DriftReport":
        if not d:
            return cls()
        known = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in d.items() if k in known}
        return cls(**filtered)
