# router.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from .motifs import MotifRegistry, cosine

DEFAULT_DOMAINS = [
    "research",
    "engineering",
    "operations",
    "creative",
    "meta",
]

# Single-agent / companion mode: one shared domain is enough.
# Multi-agent hive-mind workspaces should explicitly request the domains they need.
SINGLE_AGENT_DOMAIN = "personal"

@dataclass
class DomainScore:
    domain_id: str
    score: float

class DomainRouter:
    def __init__(self, motif_registries: Dict[str, MotifRegistry], embed_dim: int) -> None:
        self.motif_registries = motif_registries
        self.embed_dim = int(embed_dim)

    def rank_domains(self, embedding: np.ndarray, top_k: int = 2) -> List[DomainScore]:
        scores: List[DomainScore] = []
        for domain_id, reg in self.motif_registries.items():
            c = reg.domain_centroid(self.embed_dim)
            if np.allclose(c, 0):
                s = 0.0
            else:
                s = cosine(embedding, c)
            scores.append(DomainScore(domain_id=domain_id, score=float(s)))
        scores.sort(key=lambda d: d.score, reverse=True)
        return scores[:top_k]
