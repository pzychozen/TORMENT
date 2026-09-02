# roles.py
"""roles.py

Soft role inference for character continuity.

Design goals:
  - Guidance signals only (never dominance).
  - Deterministic + offline (no model dependency).
  - Slow-moving: roles update gradually to avoid flip-flopping.
  - Used to tune *memory behavior* (anchors/recency bias), not persona writing.

We distinguish:
  - user_interaction roles (how the user tends to interact through this agent)
  - agent_behavior roles (optional, future)

v1 implements user_interaction roles only.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, Tuple
import json, os, time

from .pathing import approved_subdir, stable_filename

def _now_ts() -> int:
    return int(time.time())

# Coarse, user-facing roles. Keep small to avoid over-structure.
ROLES = (
    "planner",
    "explorer",
    "reflector",
    "tinkerer",
    "storyteller",
    "minimalist",
)

# Keyword heuristics (deterministic).
_KW: Dict[str, Tuple[str, ...]] = {
    "planner": (
        "plan", "planning", "schedule", "roadmap", "next step", "steps", "todo", "checklist", "milestone",
    ),
    "reflector": (
        "feel", "feeling", "meaning", "why", "purpose", "truth", "reflect", "thinking", "mind", "emotion",
    ),
    "tinkerer": (
        "code", "bug", "error", "traceback", "fix", "patch", "commit", "diff", "refactor", "module", "api",
    ),
    "storyteller": (
        "story", "character", "plot", "scene", "dialogue", "world", "lore", "chapter", "narrative",
    ),
    "minimalist": (
        "simple", "short", "concise", "minimal", "just", "only", "quick", "tl;dr", "tldr",
    ),
}

@dataclass
class RoleProfile:
    workspace_id: str
    agent_id: str
    scores: Dict[str, float]
    created_ts: int
    updated_ts: int
    samples: int

    def to_dict(self) -> Dict:
        return asdict(self)

def _default_scores() -> Dict[str, float]:
    # Start slightly biased to explorer to avoid premature anchoring.
    return {r: (0.30 if r == "explorer" else 0.10) for r in ROLES}

class RoleStore:
    def __init__(self, data_dir: str) -> None:
        self.data_dir = os.path.realpath(data_dir)
        os.makedirs(self.data_dir, exist_ok=True)

    def _path(self, workspace_id: str, agent_id: str) -> str:
        # Defense-in-depth: validate components + contain beneath data_dir.
        agent_dir = approved_subdir(
            self.data_dir,
            "workspaces",
            workspace_id,
            "agents",
            agent_id,
            mkdir=False,
        )
        p = stable_filename(agent_dir, "roles.json")
        base = os.path.realpath(self.data_dir)
        resolved = os.path.realpath(p)
        if resolved != base and not resolved.startswith(base + os.sep):
            raise ValueError(f"Role path escapes data directory: {resolved!r}")
        return resolved

    def load(
        self,
        workspace_id: str,
        agent_id: str,
        *,
        create_if_missing: bool = True,
    ) -> RoleProfile:
        """Return a role profile, optionally without materializing a default.

        Native public cognition may consult retained role evidence, but it
        cannot use a missing profile as permission to write into the frozen
        legacy workspace.  The ordinary legacy owner preserves its historical
        materialization behavior through the default argument.
        """

        p = self._path(workspace_id, agent_id)
        if not os.path.exists(p):
            rp = RoleProfile(workspace_id=workspace_id, agent_id=agent_id, scores=_default_scores(), created_ts=_now_ts(), updated_ts=_now_ts(), samples=0)
            if create_if_missing:
                self.save(rp)
            return rp
        with open(p, "r", encoding="utf-8") as f:
            obj = json.load(f)
        scores = {r: float(obj.get("scores", {}).get(r, 0.0)) for r in ROLES}
        return RoleProfile(
            workspace_id=workspace_id,
            agent_id=agent_id,
            scores=scores or _default_scores(),
            created_ts=int(obj.get("created_ts", _now_ts())),
            updated_ts=int(obj.get("updated_ts", _now_ts())),
            samples=int(obj.get("samples", 0)),
        )

    def save(self, rp: RoleProfile) -> None:
        p = self._path(rp.workspace_id, rp.agent_id)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        rp.updated_ts = _now_ts()
        with open(p, "w", encoding="utf-8") as f:
            json.dump(rp.to_dict(), f, indent=2, sort_keys=True)

    def update_from_text(self, rp: RoleProfile, text: str) -> RoleProfile:
        """Update role scores from a single text sample (slow EMA)."""
        t = (text or "").lower()
        if not t.strip():
            return rp

        # Heuristic raw scores.
        raw = {r: 0.0 for r in ROLES}
        for role, kws in _KW.items():
            for kw in kws:
                if kw in t:
                    raw[role] += 1.2 if " " in kw else 1.0

        # If nothing matched, count as explorer sample (curiosity / novelty).
        if max(raw.values()) <= 0.0:
            raw["explorer"] = 1.0

        # Normalize raw to a distribution.
        s = sum(raw.values())
        dist = {r: (raw[r] / s if s > 0 else 0.0) for r in ROLES}

        # EMA parameters.
        try:
            ema = float(os.getenv("TORMENT_ROLE_EMA", "0.18"))
        except Exception:
            ema = 0.18
        ema = max(0.02, min(0.5, ema))

        # Update scores.
        for r in ROLES:
            rp.scores[r] = float((1.0 - ema) * float(rp.scores.get(r, 0.0)) + ema * float(dist.get(r, 0.0)))
        rp.samples = int(rp.samples) + 1
        return rp

def dominant_role(rp: RoleProfile) -> str:
    if not rp or not rp.scores:
        return "explorer"
    return max(rp.scores.items(), key=lambda kv: float(kv[1]))[0]

def role_multipliers(role: str) -> Dict[str, float]:
    """Return gentle multipliers for continuity features."""
    # Multipliers:
    # - anchor_count_mult: higher -> fewer anchors
    # - anchor_gap_mult: higher -> anchors less often
    # Keep them mild.
    r = (role or "").strip().lower()
    if r == "minimalist":
        return {"anchor_count_mult": 1.35, "anchor_gap_mult": 1.40}
    if r == "planner":
        return {"anchor_count_mult": 1.15, "anchor_gap_mult": 1.10}
    if r == "reflector":
        return {"anchor_count_mult": 0.90, "anchor_gap_mult": 0.90}
    if r == "storyteller":
        return {"anchor_count_mult": 0.95, "anchor_gap_mult": 1.00}
    if r == "tinkerer":
        return {"anchor_count_mult": 1.05, "anchor_gap_mult": 1.05}
    # explorer default: slightly more anchors.
    return {"anchor_count_mult": 0.95, "anchor_gap_mult": 0.95}
