"""Inert prompt-inclusion observation helper (observation-only).

A pure, side-effect-free helper that inspects ALREADY-RENDERED, explicitly
supplied model-visible text plus a final response text, and — only when every
selected admitted item's text is observed inside the captured model-visible text
— composes the existing audit evidence packet from those caller-supplied item
dicts.

It is CALLED NOWHERE in production. It renders nothing, performs no I/O, makes no
network or inference call, stores nothing, mutates no input, and routes its
result nowhere. When inclusion is not observed (or no usable response text is
supplied), the packet is omitted (returns ``None``); omission carries no negative
meaning, and the helper does not raise in that case.

Inputs are explicit and caller-rendered:
    * ``system_prompt`` — already-rendered system text;
    * ``messages`` — already-rendered message dicts (string content only);
    * ``admitted_context_items`` — pre-extracted selected item dicts;
    * ``response_text`` — the final produced response text.

Imports only ``__future__`` / ``typing`` and the existing packet composition
helper ``build_audit_evidence_sidecar_from_items``.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from .audit_evidence_sidecar import build_audit_evidence_sidecar_from_items


def _captured_model_visible_text(system_prompt, messages) -> str:
    """Join the explicitly supplied, already-rendered model-visible text. No
    template rendering and no I/O. Only primitive string message content is
    used; non-string content is skipped."""
    parts: List[str] = []
    if isinstance(system_prompt, str) and system_prompt:
        parts.append(system_prompt)
    if isinstance(messages, list):
        for m in messages:
            if isinstance(m, dict):
                content = m.get("content")
                if isinstance(content, str) and content:
                    parts.append(content)
    return "\n".join(parts)


def _item_text(item) -> Optional[str]:
    """Return an item's text from a single simple field only (no metadata
    crawling): prefer ``text``, then ``summary``; otherwise ``None``."""
    if not isinstance(item, dict):
        return None
    t = item.get("text")
    if isinstance(t, str) and t:
        return t
    s = item.get("summary")
    if isinstance(s, str) and s:
        return s
    return None


def observe_prompt_inclusion_packet(
    *,
    system_prompt: str,
    messages: List[Dict[str, object]],
    admitted_context_items: List[Dict[str, object]],
    response_text: str,
) -> Optional[Dict[str, object]]:
    """Observation-only: compose the existing audit evidence packet ONLY when
    every selected admitted item's text is observed in the captured model-visible
    text. Returns the existing packet, or ``None`` (packet omitted).

    Pure and inert: renders nothing, performs no I/O, stores nothing, mutates no
    input, routes nothing, and is called nowhere in production. Returning
    ``None`` (packet omitted) is non-punitive and never raises.
    """
    # A usable final response is required.
    if not isinstance(response_text, str) or not response_text.strip():
        return None

    # Capture the model-visible text from the explicit, already-rendered inputs.
    captured = _captured_model_visible_text(system_prompt, messages)

    # Every selected item's text must be observed (exact substring) in the
    # captured text; otherwise the packet is omitted. No fuzzy matching.
    for item in (admitted_context_items or []):
        text = _item_text(item)
        if text is None:
            return None
        if text not in captured:
            return None

    # Inclusion observed: compose the existing packet from explicit inputs only.
    return build_audit_evidence_sidecar_from_items(response_text, admitted_context_items)
