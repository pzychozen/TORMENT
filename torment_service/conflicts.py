# conflicts.py
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
import os, json, time, uuid


def _now_ts() -> int:
    return int(time.time())


def _validate_path_component(value: str, label: str) -> str:
    if not value or ".." in value or "/" in value or "\\" in value:
        raise ValueError(f"Invalid {label}: must not contain path separators or '..'")
    return value


def _ensure_within_base(path: str, base_dir: str) -> str:
    base = os.path.realpath(base_dir)
    resolved = os.path.realpath(path)
    if resolved != base and not resolved.startswith(base + os.sep):
        raise ValueError("Path escapes base directory")
    return resolved


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


class ConflictRegistry:
    """Append-only canon conflict registry per workspace+domain."""

    def __init__(self, data_dir: str, workspace_id: str, domain_id: str) -> None:
        self.data_dir = os.path.realpath(data_dir)
        self.workspace_id = _validate_path_component(workspace_id, "workspace_id")
        self.domain_id = _validate_path_component(domain_id, "domain_id")
        root = _ensure_within_base(
            os.path.join(self.data_dir, "workspaces", self.workspace_id, "domains", self.domain_id),
            self.data_dir,
        )
        os.makedirs(root, exist_ok=True)
        self.path = _ensure_within_base(os.path.join(root, "conflicts.jsonl"), root)
        self.events_path = _ensure_within_base(os.path.join(root, "conflict_events.jsonl"), root)

    def add(self, eid_a: int, eid_b: int, sim: float, conflict_score: float, reason: str) -> CanonConflict:
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
        )
        with open(self.path, "a", encoding="utf-8") as f:
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
        with open(self.events_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(evt, ensure_ascii=False) + "\n")

    def apply_events(self) -> Dict[str, CanonConflict]:
        latest: Dict[str, CanonConflict] = {}
        if os.path.exists(self.path):
            with open(self.path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    obj = json.loads(line)
                    c = CanonConflict(**obj)
                    latest[c.conflict_id] = c
        if os.path.exists(self.events_path):
            with open(self.events_path, "r", encoding="utf-8") as f:
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
