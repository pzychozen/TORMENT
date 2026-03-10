# scoring.py
from __future__ import annotations
from typing import Any, Dict, List, Tuple
import numpy as np
from .motifs import cosine

def score_hit(
    sim: float,
    strength: float,
    recency_days: float,
    motif_alignment: float,
    contradiction_risk: float,
    alpha: float = 0.35,
    beta: float = 0.10,
    gamma: float = 0.20,
    delta: float = 0.30,
    type_bonus: float = 0.0,
) -> float:
    rec_bonus = 1.0 / (1.0 + max(0.0, recency_days))
    base = float(sim * (1.0 + alpha*strength + beta*rec_bonus + gamma*motif_alignment) - delta*contradiction_risk)
    return float(base + float(type_bonus))
