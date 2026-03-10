# bridges.py
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple
import os, json, time
import numpy as np
from .motifs import cosine, MotifRegistry

def _now_ts() -> int:
    return int(time.time())

@dataclass
class Bridge:
    from_domain: str
    from_motif: str
    to_domain: str
    to_motif: str
    confidence: float
    created_ts: int
    status: str = "suggested"  # suggested|approved|rejected
    updated_ts: int = 0

class BridgeRegistry:
    def __init__(self, data_dir: str, workspace_id: str) -> None:
        self.data_dir = data_dir
        self.workspace_id = workspace_id
        self.path = os.path.join(self.data_dir, "workspaces", workspace_id, "bridges.json")
        self.events_path = os.path.join(self.data_dir, "workspaces", workspace_id, "bridge_events.jsonl")
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self.bridges: List[Bridge] = []
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self.path):
            return
        with open(self.path, "r", encoding="utf-8") as f:
            obj = json.load(f)
        tmp = []
        for b in obj.get("bridges", []):
            if "status" not in b:
                b["status"] = "suggested"
            if "updated_ts" not in b:
                b["updated_ts"] = b.get("created_ts", _now_ts())
            tmp.append(Bridge(**b))
        self.bridges = tmp

    def save(self) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump({"bridges": [asdict(b) for b in self.bridges]}, f, indent=2, sort_keys=True)


    def _log_event(self, evt: Dict[str, Any]) -> None:
        evt = dict(evt)
        evt.setdefault("ts", _now_ts())
        evt.setdefault("workspace_id", self.workspace_id)
        with open(self.events_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(evt, ensure_ascii=False) + "\n")
    def suggest(self, regs: Dict[str, MotifRegistry], sim_threshold: float = 0.82, max_new: int = 10) -> List[Bridge]:
        # Simple pass: compare motif centroids across domains.
        new: List[Bridge] = []
        domains = list(regs.keys())
        for i in range(len(domains)):
            for j in range(i+1, len(domains)):
                da, db = domains[i], domains[j]
                ra, rb = regs[da], regs[db]
                for ma in ra.motifs.values():
                    ca = ma.centroid_np()
                    for mb in rb.motifs.values():
                        cb = mb.centroid_np()
                        if ca.size == 0 or cb.size == 0 or ca.size != cb.size:
                            continue
                        s = cosine(ca, cb)
                        if s >= sim_threshold:
                            b = Bridge(from_domain=da, from_motif=ma.motif_id, to_domain=db, to_motif=mb.motif_id, confidence=float(s), created_ts=_now_ts(), status="suggested", updated_ts=_now_ts())
                            if not self._exists(b):
                                new.append(b)
                                if len(new) >= max_new:
                                    break
                    if len(new) >= max_new:
                        break
        if new:
            self.bridges.extend(new)
            self.save()
            for b in new:
                self._log_event({"type": "BRIDGE_SUGGEST", "from_domain": b.from_domain, "from_motif": b.from_motif, "to_domain": b.to_domain, "to_motif": b.to_motif, "confidence": float(b.confidence), "status": b.status})
        return new

    def _exists(self, b: Bridge) -> bool:
        for x in self.bridges:
            if (x.from_domain, x.from_motif, x.to_domain, x.to_motif) == (b.from_domain, b.from_motif, b.to_domain, b.to_motif):
                return True
            if (x.from_domain, x.from_motif, x.to_domain, x.to_motif) == (b.to_domain, b.to_motif, b.from_domain, b.from_motif):
                return True
        return False



    def update_confidence(self, from_domain: str, from_motif: str, to_domain: str, to_motif: str, delta: float) -> bool:
        """
        Adjust confidence for an existing bridge. Returns True if updated.
        Confidence is clipped to [0.0, 1.0]. Writes through to disk.
        """
        for b in self.bridges:
            if (b.from_domain, b.from_motif, b.to_domain, b.to_motif) == (from_domain, from_motif, to_domain, to_motif) or \
               (b.from_domain, b.from_motif, b.to_domain, b.to_motif) == (to_domain, to_motif, from_domain, from_motif):
                if b.status == "rejected":
                    return False
                b.confidence = float(max(0.0, min(1.0, b.confidence + float(delta))))
                b.updated_ts = _now_ts()
                self.save()
                return True
        return False

    
    def decide(self, from_domain: str, from_motif: str, to_domain: str, to_motif: str, decision: str) -> bool:
        """Manually approve/reject a bridge. decision: approve|reject|reset."""
        decision = decision.lower().strip()
        for b in self.bridges:
            if (b.from_domain, b.from_motif, b.to_domain, b.to_motif) == (from_domain, from_motif, to_domain, to_motif) or \
               (b.from_domain, b.from_motif, b.to_domain, b.to_motif) == (to_domain, to_motif, from_domain, from_motif):
                if decision == "approve":
                    b.status = "approved"
                elif decision == "reject":
                    b.status = "rejected"
                elif decision == "reset":
                    b.status = "suggested"
                else:
                    return False
                b.updated_ts = _now_ts()
                self.save()
                return True
        return False


    def decay(self, rate: float = 0.0005) -> None:
        """
        Gentle global decay of bridge confidence (to prevent stale bridges from persisting forever).
        """
        changed = False
        for b in self.bridges:
            newc = b.confidence * (1.0 - rate)
            if abs(newc - b.confidence) > 1e-12:
                b.confidence = float(newc)
                changed = True
        if changed:
            # prune extremely weak bridges
            self.bridges = [b for b in self.bridges if b.confidence >= 0.15]
            self.save()

    def relevant_to_domains(self, domains: List[str], top_k: int = 8) -> List[Dict[str, Any]]:
        domset = set(domains)
        rel = [b for b in self.bridges if b.from_domain in domset or b.to_domain in domset]
        rel.sort(key=lambda b: b.confidence, reverse=True)
        return [asdict(b) for b in rel[:top_k]]