"""
coherence_field.py — TORMENT structural epistemic layer v1
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Sequence, Tuple
import numpy as np


def _clip(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, float(x)))


def _unit(v: Sequence[float]) -> np.ndarray:
    a = np.asarray(v, dtype=np.float32).reshape(-1)
    n = float(np.linalg.norm(a) + 1e-12)
    return (a / n).astype(np.float32)


def cosine(a: Sequence[float], b: Sequence[float]) -> float:
    aa = _unit(a)
    bb = _unit(b)
    return float(np.dot(aa, bb))


def _member_count(m: Dict[str, Any]) -> int:
    v = m.get("members", 0)
    if isinstance(v, list):
        return len(v)
    try:
        return int(v)
    except Exception:
        return 0


def _density_from_members(member_count: int) -> float:
    # Basin depth extends to 128 members — epistemic principle:
    # deeper basins (more reinforcing observations) remain distinguishable
    return float(min(1.0, np.log1p(max(0, member_count)) / np.log(129.0)))


@dataclass
class MotifFieldState:
    motif_id: str
    label: str
    members: int
    density: float
    strength: float
    stability_score: float
    radius: float
    phi: float
    tension: float
    kappa: float
    role: str
    neighbor_count: int
    top_neighbor: Optional[str]
    top_neighbor_sim: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CoherenceField:
    W_STRENGTH = 0.42
    W_DENSITY = 0.26
    W_STABILITY = 0.24

    W_RADIUS = 0.42
    W_OVERLAP = 0.33
    W_IMBALANCE = 0.15

    NEIGHBOR_SIM_THRESHOLD = 0.55
    K_NEIGHBORS = 5

    BASIN_KAPPA_MAX = -0.015
    RIDGE_KAPPA_MIN = 0.015
    TENSION_HIGH = 0.45

    def __init__(self, motifs: Sequence[Dict[str, Any]]) -> None:
        self.motifs_raw = list(motifs or [])
        self._prepared: List[Dict[str, Any]] = self._prepare(self.motifs_raw)

    def _prepare(self, motifs: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for m in motifs:
            centroid = m.get("centroid")
            if centroid is None:
                continue
            try:
                c = _unit(centroid)
            except Exception:
                continue
            members = _member_count(m)
            density = _density_from_members(members)
            strength = _clip(float(m.get("strength", 0.0) or 0.0), 0.0, 1.0)
            stability = _clip(float(m.get("stability_score", 0.0) or 0.0), 0.0, 1.0)
            radius = _clip(float(m.get("radius", 0.0) or 0.0), 0.0, 1.0)
            out.append({
                "motif_id": str(m.get("motif_id", "")),
                "label": str(m.get("label", m.get("motif_id", ""))),
                "centroid": c,
                "members": members,
                "density": density,
                "strength": strength,
                "stability_score": stability,
                "radius": radius,
            })
        return out

    def _neighbors(self, i: int) -> List[Tuple[int, float]]:
        if i < 0 or i >= len(self._prepared):
            return []
        ci = self._prepared[i]["centroid"]
        sims: List[Tuple[int, float]] = []
        for j, m in enumerate(self._prepared):
            if i == j:
                continue
            s = float(np.dot(ci, m["centroid"]))
            if s >= self.NEIGHBOR_SIM_THRESHOLD:
                sims.append((j, s))
        sims.sort(key=lambda t: t[1], reverse=True)
        return sims[: self.K_NEIGHBORS]

    def _reinforcement(self, m: Dict[str, Any]) -> float:
        return float(
            self.W_STRENGTH * m["strength"] +
            self.W_DENSITY * m["density"] +
            self.W_STABILITY * m["stability_score"]
        )

    def _overlap_pressure(self, i: int, neighbors: List[Tuple[int, float]]) -> float:
        if not neighbors:
            return 0.0
        mi = self._prepared[i]
        base_mass = 0.50 * mi["strength"] + 0.30 * mi["density"] + 0.20 * mi["stability_score"]
        pressures = []
        for j, sim in neighbors:
            mj = self._prepared[j]
            mass_j = 0.50 * mj["strength"] + 0.30 * mj["density"] + 0.20 * mj["stability_score"]
            balance = 1.0 - abs(base_mass - mass_j)
            pressures.append(_clip(sim, 0.0, 1.0) * _clip(balance, 0.0, 1.0))
        return float(sum(pressures) / max(1, len(pressures)))

    def _imbalance_pressure(self, i: int, neighbors: List[Tuple[int, float]]) -> float:
        if not neighbors:
            return 0.0
        mi = self._prepared[i]
        my_members = max(1, mi["members"])
        vals = []
        for j, sim in neighbors:
            mj = self._prepared[j]
            ratio = max(my_members, mj["members"]) / max(1.0, min(my_members, max(1, mj["members"])))
            ratio = min(ratio, 12.0)
            vals.append(_clip((ratio - 1.0) / 11.0, 0.0, 1.0) * _clip(sim, 0.0, 1.0))
        return float(sum(vals) / max(1, len(vals)))

    def _tension(self, i: int, neighbors: List[Tuple[int, float]]) -> float:
        m = self._prepared[i]
        overlap = self._overlap_pressure(i, neighbors)
        imbalance = self._imbalance_pressure(i, neighbors)
        return float(
            self.W_RADIUS * m["radius"] +
            self.W_OVERLAP * overlap +
            self.W_IMBALANCE * imbalance
        )

    def compute(self) -> List[Dict[str, Any]]:
        if not self._prepared:
            return []

        phis: List[float] = []
        tensions: List[float] = []
        neighbor_cache: List[List[Tuple[int, float]]] = []

        for i, m in enumerate(self._prepared):
            nbrs = self._neighbors(i)
            neighbor_cache.append(nbrs)
            R = self._reinforcement(m)
            T = self._tension(i, nbrs)
            phi = _clip(R - T, -1.0, 1.0)
            phis.append(phi)
            tensions.append(T)

        out: List[Dict[str, Any]] = []
        for i, m in enumerate(self._prepared):
            nbrs = neighbor_cache[i]
            if nbrs:
                kappa = float(sum(phis[j] - phis[i] for j, _ in nbrs) / len(nbrs))
            else:
                kappa = 0.0

            role = "plateau"
            if kappa <= self.BASIN_KAPPA_MAX and tensions[i] < self.TENSION_HIGH:
                role = "basin"
            elif kappa >= self.RIDGE_KAPPA_MIN or tensions[i] >= self.TENSION_HIGH:
                role = "ridge"

            top_neighbor = None
            top_neighbor_sim = 0.0
            if nbrs:
                top_neighbor = self._prepared[nbrs[0][0]]["motif_id"]
                top_neighbor_sim = float(nbrs[0][1])

            state = MotifFieldState(
                motif_id=m["motif_id"],
                label=m["label"],
                members=m["members"],
                density=m["density"],
                strength=m["strength"],
                stability_score=m["stability_score"],
                radius=m["radius"],
                phi=phis[i],
                tension=tensions[i],
                kappa=kappa,
                role=role,
                neighbor_count=len(nbrs),
                top_neighbor=top_neighbor,
                top_neighbor_sim=top_neighbor_sim,
            )
            out.append(state.to_dict())

        out.sort(key=lambda r: (float(r["phi"]), -float(r["tension"])), reverse=True)
        return out

    def summary(self) -> Dict[str, Any]:
        rows = self.compute()
        if not rows:
            return {
                "count": 0,
                "basins": 0,
                "ridges": 0,
                "plateaus": 0,
                "phi_mean": 0.0,
                "tension_mean": 0.0,
                "kappa_mean": 0.0,
            }

        roles = [r["role"] for r in rows]
        phi_mean = float(sum(float(r["phi"]) for r in rows) / len(rows))
        tension_mean = float(sum(float(r["tension"]) for r in rows) / len(rows))
        kappa_mean = float(sum(float(r["kappa"]) for r in rows) / len(rows))

        return {
            "count": len(rows),
            "basins": sum(1 for x in roles if x == "basin"),
            "ridges": sum(1 for x in roles if x == "ridge"),
            "plateaus": sum(1 for x in roles if x == "plateau"),
            "phi_mean": phi_mean,
            "tension_mean": tension_mean,
            "kappa_mean": kappa_mean,
        }


def compute_coherence_field(motifs: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return CoherenceField(motifs).compute()


def summarize_coherence_field(motifs: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    return CoherenceField(motifs).summary()
