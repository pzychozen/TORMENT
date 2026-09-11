# identity.py
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional
import json, os, time

from .pathing import approved_subdir, stable_filename
from . import external_owner_json as _owner_json
from .atomic_publication import publish_if_absent


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


class PersistentIdentityCollisionError(RuntimeError):
    """A requested logical ID resolves to a differently declared stored identity."""


class PersistentIdentityMissingError(RuntimeError):
    """Canonical agent memory exists but its persistent identity is absent."""


class IdentityStore:
    """Persists agent identities as JSON files."""
    def __init__(self, data_dir: str) -> None:
        self.data_dir = os.path.realpath(data_dir)
        os.makedirs(self.data_dir, exist_ok=True)

    def _path(self, workspace_id: str, agent_id: str) -> str:
        # Defense-in-depth: validate dynamic components and contain the
        # resulting path beneath data_dir at the path-builder, so every sink
        # (load/save/create) is reached only via a contained path rather than
        # relying solely on upstream caller validation.
        agent_dir = approved_subdir(
            self.data_dir,
            "workspaces",
            workspace_id,
            "agents",
            agent_id,
            mkdir=False,
        )
        p = stable_filename(agent_dir, "identity.json")
        base = os.path.realpath(self.data_dir)
        resolved = os.path.realpath(p)
        if resolved != base and not resolved.startswith(base + os.sep):
            raise ValueError(f"Identity path escapes data directory: {resolved!r}")
        return resolved

    def _onboarding_path(self, workspace_id: str, agent_id: str) -> str:
        _owner_json.logical_id(workspace_id, "workspace_id")
        _owner_json.logical_id(agent_id, "agent_id")
        return _owner_json.require_exact_owner_path(
            self._path(workspace_id, agent_id),
            os.path.join(self.data_dir, "workspaces", workspace_id, "agents", agent_id, "identity.json"),
        )

    @staticmethod
    def identity_from_strict_json(raw: bytes) -> AgentIdentity:
        """Decode complete onboarding evidence without runtime fallback/defaults."""
        from .substrate.genesis_contracts import IDENTITY_SEED_KEYS, INITIAL_OVERLAY_KEYS

        value = _owner_json.strict_object(raw)
        _owner_json.exact_keys(value, AgentIdentity.__dataclass_fields__, "identity")
        for key in ("workspace_id", "agent_id"):
            _owner_json.logical_id(value[key], key)
        created = _owner_json.integer(value["created_ts"], "created_ts")
        _owner_json.integer(value["updated_ts"], "updated_ts", minimum=created)
        seed = value["seed"]
        _owner_json.require(type(seed) is dict, "identity seed must be an object")
        enabled = bool(seed.get("seed_id") or seed.get("seed_text"))
        _owner_json.exact_keys(seed, (IDENTITY_SEED_KEYS + (" character_name" if enabled else "")).split(), "identity seed")
        _owner_json.require(type(seed["core_traits"]) is list, "core_traits must be an array")
        for trait in seed["core_traits"]:
            _owner_json.nonempty_text(trait, "core trait")
        weights = seed["priority_weights"]
        _owner_json.require(type(weights) is dict, "priority_weights must be an object")
        for key, weight in weights.items():
            _owner_json.nonempty_text(key, "priority key")
            _owner_json.require(type(weight) in (int, float), "priority weights must be numeric")
        _owner_json.nonempty_text(seed["coupling_mode"], "coupling_mode")
        _owner_json.require(type(seed["coupling_strength"]) in (int, float), "coupling strength must be numeric")
        if enabled:
            _owner_json.logical_id(seed["seed_id"], "seed_id")
            _owner_json.nonempty_text(seed["seed_text"], "seed_text")
            _owner_json.nonempty_text(seed["character_name"], "character_name")
        else:
            _owner_json.require(seed["seed_id"] == "" and seed["seed_text"] == "", "invalid disabled seed declaration")
        overlay = _owner_json.exact_keys(value["overlay"], INITIAL_OVERLAY_KEYS.split(), "identity overlay")
        _owner_json.require(all(type(v) in (int, float) for v in overlay.values()), "overlay values must be numeric")
        return AgentIdentity(**value)

    @staticmethod
    def stable_identity_projection(ident: AgentIdentity) -> Dict[str, Any]:
        """Continuing I1 witness: mutable overlay and updated_ts are excluded."""
        value = ident.to_dict()
        return {key: value[key] for key in ("workspace_id", "agent_id", "seed", "created_ts")}

    def read_strict_for_onboarding(self, workspace_id: str, agent_id: str) -> Optional[AgentIdentity]:
        raw = _owner_json.read_optional_owner(self._onboarding_path(workspace_id, agent_id))
        if raw is None:
            return None
        existing = self.identity_from_strict_json(raw)
        _owner_json.require(existing.workspace_id == workspace_id and existing.agent_id == agent_id,
                            "persistent identity declaration conflicts with requested IDs")
        return existing

    def create_or_verify_for_onboarding(self, expected_identity: AgentIdentity) -> AgentIdentity:
        """Publish the exact expanded initial identity once, without time calls.

        I1 records one identity_created_ts. It initializes both persisted time
        fields. Later runtime updates are checked by verify_stable_for_onboarding,
        not silently accepted as an initial-state replay by this method.
        """
        _owner_json.require(isinstance(expected_identity, AgentIdentity), "expected identity must be typed")
        expected = self.identity_from_strict_json(_owner_json.owner_bytes(expected_identity.to_dict()))
        _owner_json.require(expected.updated_ts == expected.created_ts, "initial identity timestamps must match")
        path = self._onboarding_path(expected.workspace_id, expected.agent_id)
        existing = self.read_strict_for_onboarding(expected.workspace_id, expected.agent_id)
        if existing is None:
            parent = os.path.realpath(os.path.dirname(path))
            _owner_json.require(parent.startswith(self.data_dir + os.sep), "identity escaped data root")
            os.makedirs(parent, exist_ok=True)
            publish_if_absent(path, _owner_json.owner_bytes(expected.to_dict()))
            existing = self.read_strict_for_onboarding(expected.workspace_id, expected.agent_id)
        _owner_json.require(existing is not None and _owner_json.exact_json(existing.to_dict()) ==
                            _owner_json.exact_json(expected.to_dict()), "initial identity conflicts with intent")
        return existing

    def verify_stable_for_onboarding(self, expected_identity: AgentIdentity) -> AgentIdentity:
        """Read-only stable witness verification, separate from initial equality."""
        _owner_json.require(isinstance(expected_identity, AgentIdentity), "expected identity must be typed")
        expected = self.identity_from_strict_json(_owner_json.owner_bytes(expected_identity.to_dict()))
        existing = self.read_strict_for_onboarding(expected.workspace_id, expected.agent_id)
        _owner_json.require(existing is not None and _owner_json.exact_json(self.stable_identity_projection(existing)) ==
                            _owner_json.exact_json(self.stable_identity_projection(expected)), "stable identity conflicts with intent")
        return existing

    def load(self, workspace_id: str, agent_id: str) -> Optional[AgentIdentity]:
        p = self._path(workspace_id, agent_id)
        if not os.path.exists(p):
            return None
        with open(p, "r", encoding="utf-8") as f:
            obj = json.load(f)
        persisted_workspace_id = obj.get("workspace_id") if isinstance(obj, dict) else None
        persisted_agent_id = obj.get("agent_id") if isinstance(obj, dict) else None
        if (
            not isinstance(persisted_workspace_id, str)
            or not isinstance(persisted_agent_id, str)
            or persisted_workspace_id != workspace_id
            or persisted_agent_id != agent_id
        ):
            raise PersistentIdentityCollisionError(
                "Persistent identity collision: requested "
                f"workspace_id={workspace_id!r}, agent_id={agent_id!r}; "
                "stored declaration does not exactly match"
            )
        return AgentIdentity(
            workspace_id=persisted_workspace_id,
            agent_id=persisted_agent_id,
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
