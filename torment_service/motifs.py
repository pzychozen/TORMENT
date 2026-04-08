# motifs.py  (auto-split motif sub-basins patch)
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple
import os, json, time
import numpy as np

from .embedding_store import (
    EmbeddingShardReader,
    load_embedding as _load_embedding_universal,
    _canonical_storage_root,
    _child_path,
)
from .pathing import safe_slug

def _now_ts() -> int:
    return int(time.time())

def cosine(a: np.ndarray, b: np.ndarray) -> float:
    na = float(np.linalg.norm(a) + 1e-12)
    nb = float(np.linalg.norm(b) + 1e-12)
    return float(np.dot(a, b) / (na * nb))

def _unit(v: np.ndarray) -> np.ndarray:
    v = np.asarray(v, dtype=np.float32).reshape(-1)
    n = float(np.linalg.norm(v) + 1e-12)
    return (v / n).astype(np.float32)

@dataclass
class Motif:
    motif_id: str
    domain_id: str
    label: str
    centroid: List[float]
    strength: float
    members: List[int]
    contributing_agents: List[str]
    stability_score: float
    created_ts: int
    last_active_ts: int

    def centroid_np(self) -> np.ndarray:
        return np.asarray(self.centroid, dtype=np.float32)

class MotifRegistry:
    GRAVITY_STRENGTH_W = 0.10
    GRAVITY_DENSITY_W = 0.07
    GRAVITY_STABILITY_W = 0.05

    # NEW: conservative auto-split knobs
    AUTO_SPLIT_ENABLE = True
    AUTO_SPLIT_MIN_MEMBERS = 96
    AUTO_SPLIT_RADIUS_THRESHOLD = 0.22
    AUTO_SPLIT_IMPROVEMENT_MIN = 0.08

    def __init__(
        self,
        data_dir: str,
        workspace_id: str,
        domain_id: str,
        shard_reader: Optional[EmbeddingShardReader] = None,
        entity_payload_fn: Optional[Any] = None,
    ) -> None:
        self.workspace_id = safe_slug(workspace_id, "workspace_id")
        self.domain_id = safe_slug(domain_id, "domain_id")

        self.data_dir = _canonical_storage_root(data_dir)
        motif_dir = os.path.realpath(os.path.join(self.data_dir, "workspaces", self.workspace_id, "domains", self.domain_id))
        if not motif_dir.startswith(self.data_dir + os.sep):
            raise ValueError(f"Motif path escapes base: {motif_dir!r}")
        self._motif_base = motif_dir
        os.makedirs(motif_dir, exist_ok=True)
        self.path = _child_path(motif_dir, "motifs.json")
        self.events_path = _child_path(motif_dir, "motif_events.jsonl")
        self.merges_path = _child_path(motif_dir, "motif_merges.json")
        self._merge_suggestions: Dict[str, Dict[str, Any]] = {}
        self.motifs: Dict[str, Motif] = {}
        self._next_id: int = 1  # monotonic counter — never decreases
        # Shard-aware embedding loading
        self._shard_reader = shard_reader
        # Callable: entity_payload_fn(eid) -> dict or None  (for embedding_ref lookup)
        self._entity_payload_fn = entity_payload_fn
        self._load()

    def _guard(self, path: str) -> str:
        rp = os.path.realpath(path)
        base = os.path.realpath(self._motif_base)
        if rp != base and not rp.startswith(base + os.sep):
            raise ValueError(f"Path escapes motif root: {rp!r}")
        return rp

    @staticmethod
    def _extract_id_number(motif_id: str) -> int:
        """Extract the numeric suffix from a motif ID for counter recovery."""
        # Handles both "motif_domain_0005" and "motif_domain_0003_split0006"
        import re
        nums = re.findall(r'(\d+)', motif_id)
        return max(int(n) for n in nums) if nums else 0

    def _next_motif_id(self, prefix: str = "") -> str:
        """Generate a unique motif ID using the monotonic counter."""
        p = prefix or f"motif_{self.domain_id}"
        mid = f"{p}_{self._next_id:04d}"
        self._next_id += 1
        return mid

    def _load(self) -> None:
        if not os.path.exists(self.path):
            return
        with open(self._guard(self.path), "r", encoding="utf-8") as f:
            obj = json.load(f)
        max_seen = 0
        for mid, md in obj.get("motifs", {}).items():
            self.motifs[mid] = Motif(
                motif_id=mid,
                domain_id=self.domain_id,
                label=md.get("label", mid),
                centroid=list(md.get("centroid", [])),
                strength=float(md.get("strength", 0.1)),
                members=list(md.get("members", [])),
                contributing_agents=list(md.get("contributing_agents", [])),
                stability_score=float(md.get("stability_score", 0.5)),
                created_ts=int(md.get("created_ts", _now_ts())),
                last_active_ts=int(md.get("last_active_ts", _now_ts())),
            )
            max_seen = max(max_seen, self._extract_id_number(mid))
        # Resume counter past the highest ID ever seen — never reuse
        self._next_id = max(self._next_id, max_seen + 1)
        if os.path.exists(self.merges_path):
            try:
                with open(self._guard(self.merges_path), "r", encoding="utf-8") as f:
                    ms = json.load(f)
                self._merge_suggestions = dict(ms.get("suggestions", {}))
            except Exception:
                self._merge_suggestions = {}

    def save(self) -> None:
        obj = {"motifs": {mid: asdict(m) for mid, m in self.motifs.items()}}
        with open(self._guard(self.path), "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=2, sort_keys=True)

    def save_merges(self) -> None:
        obj = {"suggestions": self._merge_suggestions}
        with open(self._guard(self.merges_path), "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=2, sort_keys=True)

    def _log_event(self, evt: Dict[str, Any]) -> None:
        evt = dict(evt)
        evt.setdefault("ts", _now_ts())
        evt.setdefault("workspace_id", self.workspace_id)
        evt.setdefault("domain_id", self.domain_id)
        with open(self._guard(self.events_path), "a", encoding="utf-8") as f:
            f.write(json.dumps(evt, ensure_ascii=False) + "\n")

    def _density(self, m: Motif) -> float:
        # Basin depth extends to 128 members — epistemic principle:
        # deeper basins (more reinforcing observations) remain distinguishable
        return float(min(1.0, np.log1p(max(0, len(m.members))) / np.log(129.0)))

    def _gravity_bonus(self, m: Motif) -> float:
        strength = float(np.clip(m.strength, 0.0, 1.0))
        density = self._density(m)
        stability = float(np.clip(m.stability_score, 0.0, 1.0))
        return float(
            self.GRAVITY_STRENGTH_W * strength
            + self.GRAVITY_DENSITY_W * density
            + self.GRAVITY_STABILITY_W * stability
        )

    def domain_centroid(self, dim: int) -> np.ndarray:
        if not self.motifs:
            return np.zeros(dim, dtype=np.float32)
        cs = []
        ws = []
        for m in self.motifs.values():
            c = m.centroid_np()
            if c.size != dim:
                continue
            w = max(1e-6, float(m.strength)) * (1.0 + self._gravity_bonus(m))
            cs.append(c)
            ws.append(w)
        if not cs:
            return np.zeros(dim, dtype=np.float32)
        W = np.asarray(ws, dtype=np.float32)
        C = np.vstack(cs)
        out = (C * W[:, None]).sum(axis=0) / (W.sum() + 1e-12)
        return _unit(out)

    def _member_embedding(self, eid: int) -> Optional[np.ndarray]:
        # Try universal loader (shard → legacy fallback)
        payload: Dict[str, Any] = {}
        if self._entity_payload_fn:
            try:
                payload = self._entity_payload_fn(int(eid)) or {}
            except Exception:
                payload = {}
        vec = _load_embedding_universal(
            int(eid), payload, self._shard_reader, self.data_dir
        )
        if vec is not None:
            return _unit(vec)
        # Final fallback: direct legacy file (for backward compat)
        try:
            p = _child_path(self.data_dir, f"emb_{int(eid)}.npy")
        except ValueError:
            return None
        if not os.path.exists(p):
            return None
        try:
            return _unit(np.load(self._guard(p)))
        except Exception:
            return None

    def _motif_radius(self, m: Motif) -> float:
        c = m.centroid_np()
        if c.size == 0 or not m.members:
            return 0.0
        ds = []
        for eid in m.members:
            emb = self._member_embedding(eid)
            if emb is None or emb.size != c.size:
                continue
            ds.append(1.0 - cosine(c, emb))
        if not ds:
            return 0.0
        return float(np.mean(ds))

    def _two_means_split(self, X: np.ndarray, seed_a: int, seed_b: int, iters: int = 12) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        ca = X[seed_a].copy()
        cb = X[seed_b].copy()
        assign = np.zeros((X.shape[0],), dtype=np.int32)
        for _ in range(iters):
            da = np.sum((X - ca[None, :]) ** 2, axis=1)
            db = np.sum((X - cb[None, :]) ** 2, axis=1)
            assign = (db < da).astype(np.int32)
            if np.all(assign == 0) or np.all(assign == 1):
                break
            ca = _unit(X[assign == 0].mean(axis=0))
            cb = _unit(X[assign == 1].mean(axis=0))
        return assign, ca, cb

    def _maybe_split_motif(self, motif_id: str) -> Optional[Dict[str, Any]]:
        if not self.AUTO_SPLIT_ENABLE:
            return None
        m = self.motifs.get(motif_id)
        if m is None or len(m.members) < self.AUTO_SPLIT_MIN_MEMBERS:
            return None

        X = []
        eids = []
        for eid in m.members:
            emb = self._member_embedding(eid)
            if emb is None:
                continue
            X.append(emb)
            eids.append(int(eid))
        if len(X) < self.AUTO_SPLIT_MIN_MEMBERS:
            return None
        X = np.stack(X, axis=0).astype(np.float32)

        c = _unit(m.centroid_np())
        d = np.sum((X - c[None, :]) ** 2, axis=1)
        radius = float(np.mean(1.0 - np.clip(X @ c, -1.0, 1.0)))
        if radius < self.AUTO_SPLIT_RADIUS_THRESHOLD:
            return None

        seed_a = int(np.argmax(d))
        # farthest from seed_a
        d2 = np.sum((X - X[seed_a][None, :]) ** 2, axis=1)
        seed_b = int(np.argmax(d2))
        if seed_a == seed_b:
            return None

        assign, ca, cb = self._two_means_split(X, seed_a, seed_b)
        n0 = int(np.sum(assign == 0))
        n1 = int(np.sum(assign == 1))
        if n0 < 16 or n1 < 16:
            return None

        base_sse = float(np.sum((X - c[None, :]) ** 2))
        sse0 = float(np.sum((X[assign == 0] - ca[None, :]) ** 2))
        sse1 = float(np.sum((X[assign == 1] - cb[None, :]) ** 2))
        improved = 1.0 - ((sse0 + sse1) / (base_sse + 1e-12))
        if improved < self.AUTO_SPLIT_IMPROVEMENT_MIN:
            return None

        # rewrite original motif as cluster 0, create child motif for cluster 1
        child_mid = self._next_motif_id(prefix=f"{m.motif_id}_split")
        child_label = f"{m.label} sub-basin"

        members0 = [eids[i] for i in range(len(eids)) if assign[i] == 0]
        members1 = [eids[i] for i in range(len(eids)) if assign[i] == 1]

        m.members = members0
        m.centroid = _unit(ca).tolist()
        m.strength = float(max(0.18, min(1.0, 0.12 + 0.88 * (1.0 - np.exp(-len(m.members) / 24.0)))))
        m.last_active_ts = _now_ts()

        self.motifs[child_mid] = Motif(
            motif_id=child_mid,
            domain_id=self.domain_id,
            label=child_label,
            centroid=_unit(cb).tolist(),
            strength=float(max(0.15, min(1.0, 0.12 + 0.88 * (1.0 - np.exp(-len(members1) / 24.0))))),
            members=members1,
            contributing_agents=list(m.contributing_agents),
            stability_score=float(m.stability_score),
            created_ts=_now_ts(),
            last_active_ts=_now_ts(),
        )
        self.save()
        evt = {
            "type": "MOTIF_SPLIT",
            "parent": motif_id,
            "child": child_mid,
            "parent_members": len(members0),
            "child_members": len(members1),
            "radius_before": float(radius),
            "sse_improvement": float(improved),
        }
        self._log_event(evt)
        return evt

    def attach_or_create(
        self,
        embedding: np.ndarray,
        memory_eid: int,
        agent_id: str,
        summary: str,
        attach_threshold: float = 0.72,
    ) -> Tuple[List[str], Optional[str]]:
        embedding = _unit(embedding)
        dim = int(embedding.size)

        best_mid: Optional[str] = None
        best_raw_sim = -1.0
        best_attach_score = -1.0
        best_eff_threshold = attach_threshold

        for mid, m in self.motifs.items():
            c = m.centroid_np()
            if c.size != dim:
                continue
            raw_sim = cosine(embedding, c)
            density = self._density(m)
            gravity_bonus = self._gravity_bonus(m)
            attach_score = float(raw_sim + gravity_bonus)
            eff_threshold = float(max(0.62, attach_threshold - (0.04 * density + 0.03 * float(np.clip(m.strength, 0.0, 1.0)))))
            if attach_score > best_attach_score:
                best_attach_score = attach_score
                best_raw_sim = raw_sim
                best_mid = mid
                best_eff_threshold = eff_threshold

        if best_mid is not None and best_attach_score >= best_eff_threshold:
            m = self.motifs[best_mid]
            c = _unit(m.centroid_np())
            density = self._density(m)
            member_n = max(1, len(m.members))
            lr = float(np.clip(0.12 / np.sqrt(1.0 + member_n / 8.0), 0.025, 0.08))
            newc = _unit((1.0 - lr) * c + lr * embedding)
            m.centroid = newc.tolist()
            m.members.append(int(memory_eid))
            if agent_id not in m.contributing_agents:
                m.contributing_agents.append(agent_id)
            target_strength = float(0.12 + 0.88 * (1.0 - np.exp(-len(m.members) / 24.0)))
            m.strength = float(max(m.strength, min(1.0, target_strength)))
            m.stability_score = float(np.clip(0.90 * m.stability_score + 0.10 * max(0.0, best_raw_sim), 0.0, 1.0))
            m.last_active_ts = _now_ts()

            self.save()
            self._log_event({
                "type": "MOTIF_ATTACH",
                "motif_id": best_mid,
                "memory_eid": int(memory_eid),
                "agent_id": agent_id,
                "raw_sim": float(best_raw_sim),
                "attach_score": float(best_attach_score),
                "effective_threshold": float(best_eff_threshold),
                "density": float(density),
                "gravity_bonus": float(self._gravity_bonus(m)),
                "stability_score": float(m.stability_score),
                "strength": float(m.strength),
            })

            split_evt = self._maybe_split_motif(best_mid)
            if split_evt is not None:
                return [split_evt["parent"], split_evt["child"]], None

            return [best_mid], None

        mid = self._next_motif_id()
        label = self._label_from_summary(summary)
        self.motifs[mid] = Motif(
            motif_id=mid,
            domain_id=self.domain_id,
            label=label,
            centroid=embedding.tolist(),
            strength=0.10,
            members=[int(memory_eid)],
            contributing_agents=[agent_id],
            stability_score=0.5,
            created_ts=_now_ts(),
            last_active_ts=_now_ts(),
        )
        self.save()
        self._log_event({
            "type": "MOTIF_CREATE",
            "motif_id": mid,
            "memory_eid": int(memory_eid),
            "agent_id": agent_id,
            "label": label,
        })
        return [mid], mid

    def _label_from_summary(self, summary: str) -> str:
        s = (summary or "").strip()
        toks = [t.strip(".,:;!?()[]{}\\\"\\\'").lower() for t in s.split()]
        toks = [t for t in toks if t and len(t) > 2][:5]
        if not toks:
            return f"{self.domain_id} motif"
        return " ".join(toks)

    def entropy_report(self, target_n: int = 24) -> Dict[str, Any]:
        n = len(self.motifs)
        if n <= 1:
            return {"motif_count": n, "shannon": 0.0, "fragmentation": 0.0, "entropy_score": 0.0}
        strengths = np.asarray([max(1e-6, float(m.strength)) for m in self.motifs.values()], dtype=np.float64)
        p = strengths / (strengths.sum() + 1e-12)
        shannon = float(-(p * np.log(p + 1e-12)).sum() / (np.log(n + 1e-12)))
        fragmentation = float(min(1.0, n / float(max(1, target_n))))
        entropy_score = float(min(1.0, 0.55 * shannon + 0.45 * fragmentation))
        return {"motif_count": n, "shannon": shannon, "fragmentation": fragmentation, "entropy_score": entropy_score}

    def suggest_merges(self, sim_threshold: float = 0.93, max_suggestions: int = 20) -> List[Dict[str, Any]]:
        mids = list(self.motifs.keys())
        if len(mids) < 2:
            return []
        candidates: List[Tuple[float, str, str]] = []
        for i in range(len(mids)):
            mi = self.motifs[mids[i]]
            ci = mi.centroid_np()
            for j in range(i + 1, len(mids)):
                mj = self.motifs[mids[j]]
                cj = mj.centroid_np()
                if ci.size == 0 or cj.size == 0 or ci.size != cj.size:
                    continue
                s = cosine(ci, cj)
                if s >= sim_threshold:
                    a, b = mi.motif_id, mj.motif_id
                    candidates.append((s, a, b))
        candidates.sort(reverse=True, key=lambda t: t[0])
        out: List[Dict[str, Any]] = []
        for s, a, b in candidates[:max_suggestions]:
            sid = f"merge_{a}__{b}"
            if sid in self._merge_suggestions:
                self._merge_suggestions[sid]["sim"] = float(s)
                continue
            self._merge_suggestions[sid] = {
                "suggestion_id": sid,
                "a": a,
                "b": b,
                "sim": float(s),
                "status": "suggested",
                "created_ts": _now_ts(),
                "updated_ts": _now_ts(),
            }
            self._log_event({"type": "MOTIF_MERGE_SUGGESTED", "suggestion_id": sid, "a": a, "b": b, "sim": float(s)})
            out.append(self._merge_suggestions[sid])
        if out:
            self.save_merges()
        return out

    def list_merge_suggestions(self, status: str = "suggested", limit: int = 200) -> List[Dict[str, Any]]:
        items = list(self._merge_suggestions.values())
        if status and status != "any":
            items = [x for x in items if x.get("status") == status]
        items.sort(key=lambda x: (x.get("status"), float(x.get("sim", 0.0)), int(x.get("updated_ts", 0))), reverse=True)
        return items[:limit]

    def decide_merge(self, suggestion_id: str, decision: str, note: str = "") -> Dict[str, Any]:
        if suggestion_id not in self._merge_suggestions:
            raise ValueError("unknown suggestion_id")
        sug = self._merge_suggestions[suggestion_id]
        decision = decision.strip().lower()
        if decision not in ("approve", "reject", "reset"):
            raise ValueError("invalid decision")
        if decision == "approve":
            a = sug["a"]; b = sug["b"]
            if a not in self.motifs or b not in self.motifs:
                sug["status"] = "rejected"
                sug["updated_ts"] = _now_ts()
                self.save_merges()
                self._log_event({"type": "MOTIF_MERGE_FAILED", "suggestion_id": suggestion_id, "reason": "missing motif"})
                return sug
            ma = self.motifs[a]; mb = self.motifs[b]
            keep, drop = (ma, mb) if ma.strength >= mb.strength else (mb, ma)
            ca = keep.centroid_np(); cb = drop.centroid_np()
            if ca.size == cb.size and ca.size > 0:
                wa = max(1e-6, float(keep.strength)); wb = max(1e-6, float(drop.strength))
                newc = _unit((ca * wa + cb * wb) / (wa + wb))
                keep.centroid = newc.tolist()
            keep.members = sorted(list(set(keep.members + drop.members)))
            keep.contributing_agents = sorted(list(set(keep.contributing_agents + drop.contributing_agents)))
            keep.strength = float(min(1.0, keep.strength + 0.5 * drop.strength))
            keep.last_active_ts = _now_ts()
            del self.motifs[drop.motif_id]
            self.save()
            sug["status"] = "approved"
            sug["updated_ts"] = _now_ts()
            sug["note"] = note
            self.save_merges()
            self._log_event({"type": "MOTIF_MERGED", "suggestion_id": suggestion_id, "keep": keep.motif_id, "drop": drop.motif_id})
            return sug
        elif decision == "reject":
            sug["status"] = "rejected"
            sug["updated_ts"] = _now_ts()
            sug["note"] = note
            self.save_merges()
            self._log_event({"type": "MOTIF_MERGE_REJECTED", "suggestion_id": suggestion_id, "note": note})
            return sug
        else:
            sug["status"] = "suggested"
            sug["updated_ts"] = _now_ts()
            self.save_merges()
            self._log_event({"type": "MOTIF_MERGE_RESET", "suggestion_id": suggestion_id})
            return sug

    def update_entropy_and_suggest(self, target_n: int = 24, entropy_high: float = 0.72, sim_threshold: float = 0.93, max_suggestions: int = 20, auto_merge: bool = False, auto_merge_trigger: float = 0.80) -> Dict[str, Any]:
        rep = self.entropy_report(target_n=target_n)
        self._log_event({"type": "MOTIF_ENTROPY", **rep})
        if rep.get("entropy_score", 0.0) >= entropy_high:
            self.suggest_merges(sim_threshold=sim_threshold, max_suggestions=max_suggestions)
        if auto_merge and rep.get("entropy_score", 0.0) >= auto_merge_trigger:
            suggs = self.list_merge_suggestions(status="suggested", limit=5)
            approved = 0
            for s in suggs:
                if approved >= 2:
                    break
                if float(s.get("sim", 0.0)) >= (sim_threshold + 0.01):
                    self.decide_merge(s["suggestion_id"], "approve", note="auto-merge")
                    approved += 1
            rep["auto_merged"] = approved
        return rep

    def active(self, top_k: int = 8) -> List[Dict[str, Any]]:
        ms = sorted(
            self.motifs.values(),
            key=lambda m: (m.strength + self._gravity_bonus(m), m.last_active_ts),
            reverse=True
        )[:top_k]
        return [{
            "motif_id": m.motif_id,
            "label": m.label,
            "strength": m.strength,
            "stability_score": m.stability_score,
            "density": self._density(m),
            "gravity_bonus": self._gravity_bonus(m),
            "radius": self._motif_radius(m),
            "members": len(m.members),
        } for m in ms]
