"""OpenRouter provider adapter for the character truth bench.

OpenRouter is an OpenAI-compatible API gateway that lets you call many
underlying models (Claude, GPT, Gemini, Mistral, MythoMax, etc.) through
one base URL with one key. This adapter reuses the ``openai`` SDK and
points it at ``https://openrouter.ai/api/v1``.

Required env vars:
    OPENROUTER_API_KEY      your OpenRouter key
    OPENROUTER_BASE_URL     optional override (default: https://openrouter.ai/api/v1)

Model slugs use OpenRouter's namespaced format, e.g.:
    google/gemini-2.5-flash
    anthropic/claude-sonnet-4-5
    gryphe/mythomax-l2-13b
    mistralai/mistral-7b-instruct

Pick the slug you want via TORMENT_BENCH_MODELS, for example:
    TORMENT_BENCH_MODELS=openrouter:google/gemini-2.5-flash
"""

from __future__ import annotations

import os

from . import AdapterUnavailable, redact_provider_error_text

_DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"


class OpenRouterAdapter:
    name = "openrouter"

    def __init__(self, model: str) -> None:
        self.model = model
        key = os.environ.get("OPENROUTER_API_KEY", "").strip()
        base_url = os.environ.get("OPENROUTER_BASE_URL", "").strip() or _DEFAULT_BASE_URL
        if not key:
            raise AdapterUnavailable(
                "OpenRouter adapter selected but OPENROUTER_API_KEY is not set. "
                "Add it to torment_fabric/.env or your shell environment."
            )
        try:
            from openai import OpenAI  # type: ignore
        except ImportError as exc:
            raise AdapterUnavailable(
                "OpenRouter adapter uses the `openai` Python SDK with a custom "
                "base_url. Install it: pip install openai"
            ) from exc
        # OpenRouter recommends sending HTTP-Referer and X-Title headers so
        # your usage is attributed cleanly. They're optional but cheap.
        self._client = OpenAI(
            api_key=key,
            base_url=base_url,
            default_headers={
                "HTTP-Referer": "https://github.com/TORMENT/character-truth-bench",
                "X-Title": "TORMENT Character Truth Bench",
            },
        )

    def chat(self, system: str, messages: list[dict]) -> str:
        composed = [{"role": "system", "content": system}, *messages]
        try:
            resp = self._client.chat.completions.create(
                model=self.model,
                messages=composed,
                temperature=0.7,
                max_tokens=1024,
            )
        except Exception as exc:
            raise AdapterUnavailable(
                f"OpenRouter call failed: {redact_provider_error_text(exc)}"
            ) from exc
        return (resp.choices[0].message.content or "").strip()
