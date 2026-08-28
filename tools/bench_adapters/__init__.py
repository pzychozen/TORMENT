"""Provider adapters for the character truth bench.

Each adapter implements the ``ProviderAdapter`` protocol declared below.
Adapters are lazy — they only import their third-party SDK when
instantiated, so missing optional deps don't break ``--help`` or matrix
validation.

Convention: ``get_adapter(provider_name, model)`` is the only public
entry point. Returns an adapter instance or raises ``AdapterUnavailable``
with a clear actionable message.
"""

from __future__ import annotations

import os
from typing import Protocol


_PROVIDER_API_KEY_ENV_NAMES = (
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    "OPENROUTER_API_KEY",
)
_REDACTED_API_KEY_MARKER = "[REDACTED_API_KEY]"


def redact_provider_error_text(error: object) -> str:
    """Redact configured provider API keys from arbitrary error text."""
    text = str(error)
    for env_name in _PROVIDER_API_KEY_ENV_NAMES:
        credential = os.environ.get(env_name, "").strip()
        if credential:
            text = text.replace(credential, _REDACTED_API_KEY_MARKER)
    return text


class AdapterUnavailable(RuntimeError):
    """Raised when a requested provider adapter cannot be constructed.

    Reasons:
        - Missing API key in environment.
        - Missing third-party SDK (``openai``, ``anthropic``, etc.).
        - Unknown provider name.

    The message MUST be actionable — tell the user the exact env var or
    package they need.
    """


class ProviderAdapter(Protocol):
    name: str
    model: str

    def chat(self, system: str, messages: list[dict]) -> str:
        """Run one chat completion.

        Args:
            system: System prompt content (the bench wrapper + persona seed).
            messages: List of ``{"role": "user"|"assistant", "content": str}``.

        Returns:
            The assistant response text. No tool calls, no structured output
            for v0 — pure text in, pure text out.

        Raises:
            AdapterUnavailable: if the adapter cannot run this call (network
                refusal, auth failure, etc.). The runner catches and records
                this per cell rather than aborting the whole run.
        """


def get_adapter(provider: str, model: str) -> ProviderAdapter:
    """Construct an adapter for ``provider``. Lazy-imports the SDK."""
    p = provider.lower().strip()
    if p == "anthropic":
        from .anthropic_adapter import AnthropicAdapter
        return AnthropicAdapter(model=model)
    if p == "openrouter":
        from .openrouter_adapter import OpenRouterAdapter
        return OpenRouterAdapter(model=model)
    if p == "openai":
        # Direct OpenAI is still supported as an opt-in. OpenRouter can
        # also serve OpenAI models, so most setups won't need this.
        from .openai_adapter import OpenAIAdapter
        return OpenAIAdapter(model=model)
    if p == "opencodex":
        # Deprecated alias kept only to raise a clear redirect error.
        from .opencodex_adapter import OpenCodexAdapter
        return OpenCodexAdapter(model=model)
    raise AdapterUnavailable(
        f"Unknown provider {provider!r}. "
        f"Known: anthropic, openrouter, openai. "
        f"Add a new adapter under tools/bench_adapters/ to extend."
    )
