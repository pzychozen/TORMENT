# summarizer.py
from __future__ import annotations
import re

def summarize(text: str, max_chars: int = 320) -> str:
    """
    Deterministic placeholder summary.
    Replace with local LLM summary later.
    """
    text = (text or "").strip()
    if not text:
        return ""
    # collapse whitespace
    t = re.sub(r"\s+", " ", text)
    # take first sentence-ish chunk
    m = re.split(r"(?<=[.!?])\s+", t)
    s = m[0] if m else t
    if len(s) < 60 and len(m) > 1:
        s = (s + " " + m[1]).strip()
    if len(s) > max_chars:
        s = s[:max_chars-1].rstrip() + "…"
    return s
