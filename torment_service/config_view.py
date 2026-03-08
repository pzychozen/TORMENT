"""Config view helpers.

Provides a lightweight, UI-friendly view of Torment's effective configuration.

Goals:
- Make it easy to see "what is actually active".
- Keep it minimal: read-only, derived from env + profile defaults.
"""

from __future__ import annotations

import os
from typing import Dict, Any


# Known knobs and their built-in defaults.
# Values are stored as strings to match os.environ style.
KNOWN_DEFAULTS: Dict[str, str] = {
    # Data / service
    "TORMENT_DATA_DIR": "<auto>",

    # Embeddings
    "TORMENT_EMBED_PROVIDER": "hash",
    "TORMENT_EMBED_MODEL": "",
    "TORMENT_EMBED_DEVICE": "cpu",
    "TORMENT_EMBED_BATCH": "32",
    "TORMENT_EMBED_CACHE_SIZE": "0",
    "TORMENT_EMBED_STRICT": "0",
    "TORMENT_OLLAMA_URL": "http://127.0.0.1:11434",

    # Profiles
    "TORMENT_PROFILE": "",

    # Continuity (self-thread + thread window)
    "TORMENT_SELF_MEMORY_BONUS": "0.06",
    "TORMENT_SELF_ANCHOR_BONUS": "0.04",
    "TORMENT_THREAD_WINDOW_STEPS": "50",
    "TORMENT_THREAD_WINDOW_BONUS": "0.08",

    # Identity anchors
    "TORMENT_ID_ANCHOR_ENABLE": "1",
    "TORMENT_ID_ANCHOR_MIN_COUNT": "3",
    "TORMENT_ID_ANCHOR_MIN_GAP_STEPS": "50",
    "TORMENT_ID_ANCHOR_MAX_EXAMPLES": "2",
    "TORMENT_ID_ANCHOR_AFFECT_COUNT_MULT": "1.6",
    "TORMENT_ID_ANCHOR_AFFECT_GAP_MULT": "1.5",
    "TORMENT_ANCHOR_BOOST_TOPK": "3",
    "TORMENT_ANCHOR_BOOST_REST_MULT": "0.35",
    "TORMENT_ANCHOR_KEEP_PER_MOTIF": "1",
    "TORMENT_ANCHOR_WEAK_MEMBER_MAX": "3",
    "TORMENT_ANCHOR_WEAK_MIN_AGE_STEPS": "800",

    # Affect + mood drift
    "TORMENT_AFFECT_ENABLE": "1",
    "TORMENT_AFFECT_MATCH_BONUS": "0.05",
    "TORMENT_AFFECT_MIN_CONF": "0.40",
    "TORMENT_MOOD_DRIFT_ENABLE": "1",
    "TORMENT_MOOD_DRIFT_MIN_CONF": "0.55",
    "TORMENT_MOOD_DRIFT_MIN_GAP_STEPS": "120",
    "TORMENT_MOOD_DRIFT_HALF_LIFE_DAYS": "60",
    "TORMENT_MOOD_DRIFT_QUERY_BONUS": "0.04",

    # Mood spiral dampening
    "TORMENT_MOOD_SPIRAL_ENABLE": "1",
    "TORMENT_MOOD_SPIRAL_WINDOW_STEPS": "800",
    "TORMENT_MOOD_SPIRAL_MIN_NEG_DRIFTS": "2",
    "TORMENT_MOOD_SPIRAL_OLDER_THAN_STEPS": "250",
    "TORMENT_MOOD_SPIRAL_PENALTY_MAX": "0.08",

    # Role inference
    "TORMENT_ROLE_ENABLE": "1",
    "TORMENT_ROLE_EMA": "0.18",

    # Continuity debug
    "TORMENT_CONTINUITY_DEBUG_TOP": "5",
    "TORMENT_CONTINUITY_DEBUG_MAX_HITS": "50",

    # Jobs / maintenance
    "TORMENT_JOB_PERSIST": "0",
    "TORMENT_JOB_MAX": "50",
    "TORMENT_CLONE_MIN_GAP_S": "0",
    "TORMENT_CLONE_LOG_EVERY": "250",

    # Health / audits
    "TORMENT_HEALTH_WORKSPACE_SAMPLE": "10",
    "TORMENT_HEALTH_INCLUDE_AUDITS": "0",
    "TORMENT_HEALTH_AUDIT_SAMPLE": "10",

    # Character (living identity layer)
    "TORMENT_CHARACTER_ENABLE": "1",
    "TORMENT_CHARACTER_DRIFT_WINDOW_STEPS": "500",
    "TORMENT_CHARACTER_CORRECTION_THRESHOLD": "0.35",
    "TORMENT_CHARACTER_GRAVITY_STRENGTH": "0.12",
    "TORMENT_CHARACTER_DRIFT_CHECK_EVERY": "25",
}


def _is_truthy(val: str) -> bool:
    return str(val).strip().lower() in ("1", "true", "yes", "on")


def build_config_view(*, active_profile: str | None, profile_applied: Dict[str, str], profile_known: bool, data_dir: str) -> Dict[str, Any]:
    """Build a read-only config view for UI/debugging."""

    effective: Dict[str, Any] = {}
    for k, dflt in KNOWN_DEFAULTS.items():
        if k == "TORMENT_DATA_DIR":
            eff = data_dir
        else:
            eff = os.environ.get(k, dflt)

        source = "default"
        if active_profile and (k in profile_applied) and (str(eff) == str(profile_applied.get(k))):
            source = "profile_default"
        if k in os.environ and not (active_profile and (k in profile_applied) and (str(os.environ.get(k)) == str(profile_applied.get(k)))):
            source = "env_override"

        effective[k] = {"value": eff, "default": dflt, "source": source}

    derived = {
        "profile": {
            "name": active_profile or "",
            "known": bool(profile_known),
            "applied_count": int(len(profile_applied)),
        },
        "embed": {
            "strict": _is_truthy(os.environ.get("TORMENT_EMBED_STRICT", "0")),
            "cache_enabled": int(os.environ.get("TORMENT_EMBED_CACHE_SIZE", "0") or 0) > 0,
        },
    }

    return {"ok": True, "effective": effective, "derived": derived}
