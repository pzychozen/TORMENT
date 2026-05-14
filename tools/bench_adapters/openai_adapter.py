"""OpenAI provider adapter for the character truth bench.

Reads OPENAI_API_KEY from environment. Lazy-imports the ``openai`` SDK so
``--help`` works without the package installed.
"""

from __future__ import annotations

import os

from . import AdapterUnavailable


class OpenAIAdapter:
    name = "openai"

    def __init__(self, model: str) -> None:
        self.model = model
        key = os.environ.get("OPENAI_API_KEY", "").strip()
        if not key:
            raise AdapterUnavailable(
                "OpenAI adapter selected but OPENAI_API_KEY is not set. "
                "Set it in your .env or shell environment before running the bench."
            )
        try:
            # Lazy import — only happens when adapter is actually constructed.
            from openai import OpenAI  # type: ignore
        except ImportError as exc:
            raise AdapterUnavailable(
                "OpenAI adapter selected but the `openai` Python package is "
                "not installed. Run: pip install openai"
            ) from exc
        self._client = OpenAI(api_key=key)

    def chat(self, system: str, messages: list[dict]) -> str:
        # Compose: system + user/assistant turns. Bench v0 uses sync API.
        composed = [{"role": "system", "content": system}, *messages]
        try:
            resp = self._client.chat.completions.create(
                model=self.model,
                messages=composed,
                temperature=0.7,
                max_tokens=1024,
            )
        except Exception as exc:
            raise AdapterUnavailable(f"OpenAI call failed: {exc}") from exc
        return (resp.choices[0].message.content or "").strip()
