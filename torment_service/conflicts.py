# conflicts.py
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
import os, json, time, uuid

from .embedding_store import _canonical_storage_root, _child_path
from .pathing import safe_slug


def _now_ts() -> int:
    return int(time.time())


@dataclass
class CanonConflict:
    conflict_id: str
    workspace_id: str
    domain_id: str
    eid_a: int
    eid_b: int
    sim: float
    conflict_score: float
    reason: str
    status: str  # open|resolved|rejected|forked
    created_ts: int
    decided_ts: Optional[int] = None
    decision: Optional[str] = None
    note: Optional[str] = None
    origin_scope: Optional[str] = None
    origin_agent_id: Optional[str] = None
    origin_domain_id: Optional[str] = None


class ConflictRegistry:
    """Append-only canon conflict registry per workspace+domain."""

    def __init__(self, data_dir: str, workspace_id: str, domain_id: str) -> None:
        self.workspace_id = safe_slug(workspace_id, "workspace_id")
        self.domain_id = safe_slug(domain_id, "domain_id")

        # Canonical trust chain: data_dir → workspaces/<ws>/domains/<dom>
        self.data_dir = _canonical_storage_root(data_dir)
        domain_root = os.path.realpath(
            os.path.join(self.data_dir, "workspaces", self.workspace_id, "domains", self.domain_id)
        )
        if not domain_root.startswith(self.data_dir + os.sep):
            raise ValueError(f"Domain path escapes base: {domain_root!r}")
        os.makedirs(domain_root, exist_ok=True)
        self._base = domain_root
        self.path = _child_path(domain_root, "conflicts.jsonl")
        self.events_path = _child_path(domain_root, "conflict_events.jsonl")

    def _guard(self, path: str) -> str:
        rp = os.path.realpath(path)
        base = os.path.realpath(self._base)
        if rp != base and not rp.startswith(base + os.sep):
            raise ValueError(f"Path escapes domain root: {rp!r}")
        return rp

    def add(
        self,
        eid_a: int,
        eid_b: int,
        sim: float,
        conflict_score: float,
        reason: str,
        *,
        origin_scope: Optional[str] = None,
        origin_agent_id: Optional[str] = None,
        origin_domain_id: Optional[str] = None,
    ) -> CanonConflict:
        if origin_scope is None:
            if origin_agent_id is not None or origin_domain_id is not None:
                raise ValueError("Legacy conflict origin must not include qualifiers")
        elif origin_scope == "private":
            if not isinstance(origin_agent_id, str) or not origin_agent_id.strip():
                raise ValueError("Private conflict origin requires origin_agent_id")
            if origin_domain_id is not None:
                raise ValueError("Private conflict origin forbids origin_domain_id")
        elif origin_scope == "shared":
            if not isinstance(origin_domain_id, str) or not origin_domain_id.strip():
                raise ValueError("Shared conflict origin requires origin_domain_id")
            if origin_agent_id is not None:
                raise ValueError("Shared conflict origin forbids origin_agent_id")
        else:
            raise ValueError("Unknown conflict origin_scope")

        c = CanonConflict(
            conflict_id=str(uuid.uuid4()),
            workspace_id=self.workspace_id,
            domain_id=self.domain_id,
            eid_a=int(eid_a),
            eid_b=int(eid_b),
            sim=float(sim),
            conflict_score=float(conflict_score),
            reason=str(reason)[:240],
            status="open",
            created_ts=_now_ts(),
            origin_scope=origin_scope,
            origin_agent_id=origin_agent_id,
            origin_domain_id=origin_domain_id,
        )
        with open(self._guard(self.path), "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(c), ensure_ascii=False) + "\n")
        return c

    def decide(self, conflict_id: str, decision: str, note: str = "") -> None:
        evt = {
            "conflict_id": conflict_id,
            "workspace_id": self.workspace_id,
            "domain_id": self.domain_id,
            "decision": decision,
            "note": note,
            "ts": _now_ts(),
        }
        with open(self._guard(self.events_path), "a", encoding="utf-8") as f:
            f.write(json.dumps(evt, ensure_ascii=False) + "\n")

    def apply_events(self) -> Dict[str, CanonConflict]:
        latest: Dict[str, CanonConflict] = {}
        if os.path.exists(self.path):
            with open(self._guard(self.path), "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    obj = json.loads(line)
                    c = CanonConflict(**obj)
                    latest[c.conflict_id] = c
        if os.path.exists(self.events_path):
            with open(self._guard(self.events_path), "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    e = json.loads(line)
                    cid = e.get("conflict_id")
                    c = latest.get(cid)
                    if c is None:
                        continue
                    decision = str(e.get("decision", "")).strip().lower()
                    c.decision = decision
                    c.note = e.get("note")
                    c.decided_ts = int(e.get("ts", _now_ts()))
                    if decision in ("keep_a", "keep_b", "merge", "demote_both"):
                        c.status = "resolved"
                    elif decision == "fork":
                        c.status = "forked"
                    elif decision == "reject":
                        c.status = "rejected"
                    latest[cid] = c
        return latest

    def list(self, status: str = "open", limit: int = 200) -> List[CanonConflict]:
        allc = self.apply_events()
        out: List[CanonConflict] = []
        for c in allc.values():
            if status != "any" and c.status != status:
                continue
            out.append(c)
        out.sort(key=lambda x: x.created_ts, reverse=True)
        return out[:limit]
