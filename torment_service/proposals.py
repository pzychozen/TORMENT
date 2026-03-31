# proposals.py
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
import os, json, time, uuid
import numpy as np

def _now_ts() -> int:
    return int(time.time())

def _validate_path_component(value: str, label: str = "identifier") -> str:
    """Reject path traversal characters in user-provided identifiers."""
    if ".." in value or "/" in value or "\\" in value:
        raise ValueError(f"Invalid {label}: must not contain path separators or '..'")
    return value

@dataclass
class ShareProposal:
    proposal_id: str
    workspace_id: str
    domain_id: str
    agent_id: str
    summary: str
    embedding: List[float]
    mtype: str
    confidence: float
    strength: float
    created_ts: int
    status: str  # pending|approved|rejected
    half_life_days: Optional[float] = None
    processed_ts: Optional[int] = None
    note: Optional[str] = None

class ProposalRegistry:
    """
    Append-only JSONL store of share proposals per workspace+domain.

    We keep it simple and auditable: each proposal is written once; status updates
    are written as new records in an events file (proposals_events.jsonl).
    """
    def __init__(self, data_dir: str, workspace_id: str, domain_id: str) -> None:
        self.data_dir = data_dir
        self.workspace_id = workspace_id
        self.domain_id = domain_id
        _validate_path_component(workspace_id, "workspace_id")
        _validate_path_component(domain_id, "domain_id")
        safe_dir = os.path.normpath(data_dir)
        root = os.path.normpath(os.path.join(safe_dir, "workspaces", workspace_id, "domains", domain_id))
        if not root.startswith(safe_dir):
            raise ValueError("Path escapes data directory")
        os.makedirs(root, exist_ok=True)
        self.path = os.path.join(root, "proposals.jsonl")
        self.events_path = os.path.join(root, "proposal_events.jsonl")

    def submit(
        self,
        agent_id: str,
        summary: str,
        embedding: np.ndarray,
        mtype: str,
        confidence: float,
        strength: float,
        half_life_days: Optional[float] = None,
    ) -> ShareProposal:
        p = ShareProposal(
            proposal_id=str(uuid.uuid4()),
            workspace_id=self.workspace_id,
            domain_id=self.domain_id,
            agent_id=agent_id,
            summary=summary,
            embedding=[float(x) for x in embedding.astype("float32").tolist()],
            mtype=mtype,
            confidence=float(confidence),
            strength=float(strength),
            half_life_days=half_life_days,
            created_ts=_now_ts(),
            status="pending",
        )
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(p), ensure_ascii=False) + "\n")
        return p

    def list_pending(self, limit: int = 2000) -> List[ShareProposal]:
        """Return proposals whose *effective* status is still 'pending'.

        This replays the events file so that approved/rejected proposals
        are correctly excluded — the raw proposals.jsonl only stores the
        original submission status.
        """
        latest = self.apply_events()
        if not latest:
            return []
        pending = [p for p in latest.values() if p.status == "pending"]
        # Sort by creation time (oldest first) for stable ordering
        pending.sort(key=lambda p: p.created_ts)
        return pending[:limit]

    def mark(self, proposal_id: str, status: str, note: Optional[str] = None) -> None:
        evt = {
            "proposal_id": proposal_id,
            "workspace_id": self.workspace_id,
            "domain_id": self.domain_id,
            "status": status,
            "note": note,
            "ts": _now_ts(),
        }
        with open(self.events_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(evt, ensure_ascii=False) + "\n")

    def apply_events(self) -> Dict[str, ShareProposal]:
        """
        Rebuild latest status for proposals by replaying events.
        Returns mapping proposal_id -> latest proposal object with updated status fields.
        """
        latest: Dict[str, ShareProposal] = {}
        if os.path.exists(self.path):
            with open(self.path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    obj = json.loads(line)
                    p = ShareProposal(**obj)
                    latest[p.proposal_id] = p
        if os.path.exists(self.events_path):
            with open(self.events_path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    e = json.loads(line)
                    pid = e["proposal_id"]
                    p = latest.get(pid)
                    if p is None:
                        continue
                    p.status = e.get("status", p.status)
                    p.note = e.get("note", p.note)
                    p.processed_ts = int(e.get("ts", _now_ts()))
                    latest[pid] = p
        return latest
