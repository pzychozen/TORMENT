# identity.py
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional
import json, os, time

def _now_ts() -> int:
    return int(time.time())

DEFAULT_AGENT_SEED = {
    "core_traits": ["analytical"],
    "priority_weights": {"facts": 0.8, "projects": 0.7, "preferences": 0.4, "motifs": 0.7},
    "coupling_mode": "read_only",
    "coupling_strength": 0.25,
    # Character seed: set to a non-empty string to enable the living character layer.
    # Should be 10-15 lines of natural language describing core identity.
    "seed_text": "",
    "seed_id": "",
}

DEFAULT_AGENT_OVERLAY = {
    "write_threshold": 0.45,
    "decay_scale": 1.0,
    "promotion_bias": 0.6,
    "novelty_bias": 0.5,
    "motif_sensitivity": 0.7,
    "contradiction_sensitivity": 0.8,
    "reinforcement_gain": 0.9,
    "coupling_strength": 0.25,
    "shared_trust": 0.6,
    "stability_guard": 0.8,
}

def clamp01(x: float) -> float:
    return 0.0 if x < 0.0 else 1.0 if x > 1.0 else float(x)

def bounded_update(curr: float, delta: float, lo: float, hi: float) -> float:
    return float(min(hi, max(lo, curr + delta)))

@dataclass
class AgentIdentity:
    workspace_id: str
    agent_id: str
    seed: Dict[str, Any]
    overlay: Dict[str, float]
    created_ts: int
    updated_ts: int

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d

class IdentityStore:
    """Persists agent identities as JSON files."""
    def __init__(self, data_dir: str) -> None:
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)

    def _path(self, workspace_id: str, agent_id: str) -> str:
        return os.path.join(self.data_dir, "workspaces", workspace_id, "agents", agent_id, "identity.json")

    def load(self, workspace_id: str, agent_id: str) -> Optional[AgentIdentity]:
        p = self._path(workspace_id, agent_id)
        if not os.path.exists(p):
            return None
        with open(p, "r", encoding="utf-8") as f:
            obj = json.load(f)
        return AgentIdentity(
            workspace_id=obj["workspace_id"],
            agent_id=obj["agent_id"],
            seed=obj.get("seed", DEFAULT_AGENT_SEED),
            overlay={k: float(v) for k, v in obj.get("overlay", DEFAULT_AGENT_OVERLAY).items()},
            created_ts=int(obj.get("created_ts", _now_ts())),
            updated_ts=int(obj.get("updated_ts", _now_ts())),
        )

    def save(self, ident: AgentIdentity) -> None:
        p = self._path(ident.workspace_id, ident.agent_id)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        ident.updated_ts = _now_ts()
        with open(p, "w", encoding="utf-8") as f:
            json.dump(ident.to_dict(), f, indent=2, sort_keys=True)

    def create(self, workspace_id: str, agent_id: str, seed: Optional[Dict[str, Any]] = None) -> AgentIdentity:
        seed = seed or DEFAULT_AGENT_SEED
        ident = AgentIdentity(
            workspace_id=workspace_id,
            agent_id=agent_id,
            seed=seed,
            overlay={k: float(v) for k, v in DEFAULT_AGENT_OVERLAY.items()},
            created_ts=_now_ts(),
            updated_ts=_now_ts(),
        )
        self.save(ident)
        return ident
