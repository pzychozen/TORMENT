"""affect.py

Lightweight affect tagging for character continuity.

Design goals:
  - Cheap, deterministic, and offline.
  - Coarse tags (guidance signals) rather than a mood engine.
  - Safe defaults: returns ("neutral", 0.0) if uncertain.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Dict, Tuple


@dataclass(frozen=True)
class Affect:
    tag: str
    conf: float


# Coarse, user-facing tags.
TAGS = ("neutral", "calm", "stressed", "excited", "sad", "angry")


_KW: Dict[str, Tuple[str, ...]] = {
    "calm": (
        "calm", "okay", "ok", "stable", "grounded", "relaxed", "peaceful", "chill", "fine"
    ),
    "stressed": (
        "stressed", "stress", "anxious", "anxiety", "overwhelmed", "panic", "panicking",
        "worried", "worry", "tense", "pressure", "burnt", "burned", "tired", "exhausted"
    ),
    "excited": (
        "excited", "hyped", "thrilled", "pumped", "energized", "can't wait", "cant wait",
        "awesome", "amazing", "let's go", "lets go", "love this"
    ),
    "sad": (
        "sad", "down", "depressed", "depression", "lonely", "empty", "hopeless", "tear",
        "cry", "crying", "grief", "hurt"
    ),
    "angry": (
        "angry", "mad", "furious", "rage", "pissed", "annoyed", "irritated", "hate", "fuming"
    ),
}


_PERSONAL_PATTERNS = (
    r"\bi feel\b",
    r"\bfeeling\b",
    r"\bmy mood\b",
    r"\bi'm\b",
    r"\bi am\b",
    r"\btoday\b",
    r"\blately\b",
    r"\brecently\b",
)


def looks_personal(text: str) -> bool:
    t = (text or "").lower()
    for pat in _PERSONAL_PATTERNS:
        if re.search(pat, t):
            return True
    return False


def classify_affect(text: str) -> Affect:
    """Return a coarse affect tag and confidence in [0,1].

    Rule-based scoring:
      - count keyword matches per tag
      - pick best tag if it beats runner-up by a margin
    """
    t = (text or "").strip().lower()
    if not t:
        return Affect("neutral", 0.0)

    scores: Dict[str, float] = {k: 0.0 for k in _KW.keys()}
    for tag, kws in _KW.items():
        for kw in kws:
            if kw in t:
                # Light weighting: multi-word phrases are slightly stronger.
                scores[tag] += 1.2 if " " in kw else 1.0

    # No signal.
    best_tag = max(scores.items(), key=lambda kv: kv[1])[0]
    best = float(scores[best_tag])
    if best <= 0.0:
        return Affect("neutral", 0.0)

    # Runner-up.
    runner = sorted(scores.values(), reverse=True)[1] if len(scores) > 1 else 0.0

    # Require a minimal margin to avoid flip-flopping.
    if best < 1.0 or (best - float(runner)) < 0.75:
        return Affect("neutral", 0.0)

    # Confidence saturates quickly: 1 match -> ~0.5, 2 -> ~0.67, 3 -> ~0.75.
    conf = float(best / (best + 1.0))
    conf = max(0.0, min(1.0, conf))
    return Affect(best_tag, conf)
