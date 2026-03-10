"""Torment profiles

Profiles are a convenience layer for local users.

They set *defaults* for common tuning knobs (memory continuity, affect, etc.).
Any explicit environment variable set by the user always wins.

This is intentionally lightweight: it does not change core behavior, only
initial default values.
"""

from __future__ import annotations

import os
from typing import Dict


PROFILES: Dict[str, Dict[str, str]] = {
    # Strong continuity + gentle emotional awareness (recommended for companions)
    "companion": {
        "TORMENT_SELF_MEMORY_BONUS": "0.08",
        "TORMENT_SELF_ANCHOR_BONUS": "0.04",
        "TORMENT_THREAD_WINDOW_STEPS": "60",
        "TORMENT_THREAD_WINDOW_BONUS": "0.10",
        "TORMENT_AFFECT_ENABLE": "1",
        "TORMENT_AFFECT_MATCH_BONUS": "0.06",
        "TORMENT_AFFECT_MIN_CONF": "0.40",
        "TORMENT_MOOD_DRIFT_ENABLE": "1",
        "TORMENT_MOOD_DRIFT_QUERY_BONUS": "0.04",
        "TORMENT_MOOD_SPIRAL_ENABLE": "1",
        "TORMENT_MOOD_SPIRAL_PENALTY_MAX": "0.08",
        "TORMENT_ID_ANCHOR_MIN_COUNT": "3",
        "TORMENT_ID_ANCHOR_MIN_GAP_STEPS": "50",
        "TORMENT_ANCHOR_BOOST_TOPK": "3",
        "TORMENT_ANCHOR_BOOST_REST_MULT": "0.35",
    },
    # Low-impact, low-feature surface (for users who dislike "identity" behavior)
    "minimalist": {
        "TORMENT_SELF_MEMORY_BONUS": "0.03",
        "TORMENT_SELF_ANCHOR_BONUS": "0.02",
        "TORMENT_THREAD_WINDOW_STEPS": "30",
        "TORMENT_THREAD_WINDOW_BONUS": "0.04",
        "TORMENT_AFFECT_ENABLE": "0",
        "TORMENT_MOOD_DRIFT_ENABLE": "0",
        "TORMENT_MOOD_SPIRAL_ENABLE": "0",
        "TORMENT_ID_ANCHOR_MIN_COUNT": "6",
        "TORMENT_ID_ANCHOR_MIN_GAP_STEPS": "200",
        "TORMENT_ANCHOR_BOOST_TOPK": "1",
        "TORMENT_ANCHOR_BOOST_REST_MULT": "0.20",
    },
    # Project/task continuity (less emotion, more thread + self)
    "assistant": {
        "TORMENT_SELF_MEMORY_BONUS": "0.06",
        "TORMENT_SELF_ANCHOR_BONUS": "0.03",
        "TORMENT_THREAD_WINDOW_STEPS": "45",
        "TORMENT_THREAD_WINDOW_BONUS": "0.07",
        "TORMENT_AFFECT_ENABLE": "0",
        "TORMENT_MOOD_DRIFT_ENABLE": "0",
        "TORMENT_MOOD_SPIRAL_ENABLE": "0",
        "TORMENT_ID_ANCHOR_MIN_COUNT": "5",
        "TORMENT_ID_ANCHOR_MIN_GAP_STEPS": "120",
        "TORMENT_ANCHOR_BOOST_TOPK": "2",
        "TORMENT_ANCHOR_BOOST_REST_MULT": "0.25",
    },
    # Many agents / shared fabric; keeps personal biases low by default
    "hive": {
        "TORMENT_SELF_MEMORY_BONUS": "0.02",
        "TORMENT_SELF_ANCHOR_BONUS": "0.01",
        "TORMENT_THREAD_WINDOW_STEPS": "20",
        "TORMENT_THREAD_WINDOW_BONUS": "0.03",
        "TORMENT_AFFECT_ENABLE": "0",
        "TORMENT_MOOD_DRIFT_ENABLE": "0",
        "TORMENT_MOOD_SPIRAL_ENABLE": "0",
        "TORMENT_ID_ANCHOR_MIN_COUNT": "8",
        "TORMENT_ID_ANCHOR_MIN_GAP_STEPS": "250",
        "TORMENT_ANCHOR_BOOST_TOPK": "1",
        "TORMENT_ANCHOR_BOOST_REST_MULT": "0.15",
    },
}


def apply_profile_env(profile: str | None) -> Dict[str, str]:
    """Apply a profile by setting env defaults.

    Returns the mapping of keys that were *applied* (i.e., set because the
    user did not explicitly set them).
    """
    if not profile:
        return {}

    p = str(profile).strip().lower()
    if not p:
        return {}

    cfg = PROFILES.get(p)
    if not cfg:
        return {}

    applied: Dict[str, str] = {}
    for k, v in cfg.items():
        if k not in os.environ or os.environ.get(k) in (None, ""):
            os.environ[k] = v
            applied[k] = v
    return applied
