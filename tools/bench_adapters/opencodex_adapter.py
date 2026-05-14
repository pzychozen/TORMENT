"""DEPRECATED — kept only so old configs raise a clear error.

The bench targets OpenRouter, not OpenCodex. See ``openrouter_adapter.py``.
Selecting this provider raises immediately with a redirect message.
"""

from __future__ import annotations

from . import AdapterUnavailable


class OpenCodexAdapter:
    name = "opencodex"

    def __init__(self, model: str) -> None:
        raise AdapterUnavailable(
            "The 'opencodex' provider is deprecated for this bench. "
            "Use 'openrouter' instead. "
            "Update TORMENT_BENCH_MODELS and the matrix YAML accordingly."
        )

    def chat(self, system: str, messages: list[dict]) -> str:  # pragma: no cover
        raise AdapterUnavailable("opencodex adapter is deprecated; use openrouter")
