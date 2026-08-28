"""Anthropic provider adapter for the character truth bench.

Reads ANTHROPIC_API_KEY from environment. Lazy-imports the ``anthropic`` SDK.
"""

from __future__ import annotations

import os

from . import AdapterUnavailable, redact_provider_error_text


class AnthropicAdapter:
    name = "anthropic"

    def __init__(self, model: str) -> None:
        self.model = model
        key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
        if not key:
            raise AdapterUnavailable(
                "Anthropic adapter selected but ANTHROPIC_API_KEY is not set. "
                "Set it in your .env or shell environment before running the bench."
            )
        try:
            from anthropic import Anthropic  # type: ignore
        except ImportError as exc:
            raise AdapterUnavailable(
                "Anthropic adapter selected but the `anthropic` Python package "
                "is not installed. Run: pip install anthropic"
            ) from exc
        self._client = Anthropic(api_key=key)

    def chat(self, system: str, messages: list[dict]) -> str:
        # Anthropic separates `system` from the message turn list — clean
        # match for the bench's wrapper-as-system convention.
        try:
            resp = self._client.messages.create(
                model=self.model,
                system=system,
                messages=messages,
                temperature=0.7,
                max_tokens=1024,
            )
        except Exception as exc:
            raise AdapterUnavailable(
                f"Anthropic call failed: {redact_provider_error_text(exc)}"
            ) from exc
        # Anthropic returns content as a list of blocks; first text block wins.
        parts = []
        for block in getattr(resp, "content", []) or []:
            text = getattr(block, "text", None)
            if text:
                parts.append(text)
        return "\n".join(parts).strip()
