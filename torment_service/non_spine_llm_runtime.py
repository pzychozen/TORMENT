"""torment_service/non_spine_llm_runtime.py

Dormant, internal, NON-Spine LLM runtime SKELETON (test-callable only).

This module is the named owner shape selected ON PAPER by the separate-LLM-runtime
direction-selection frame (docs-only). It is INERT: nothing in production instantiates
or calls it. It exists so a future, separately-authorized step has a concrete, fenced
skeleton to build against.

Shape:
  - ``NonSpineLLMMemoryContext`` -- explicit, bounded, read-only memory-context package;
  - ``NonSpineLLMRuntimeRequest`` -- explicit, primitive-only input object;
  - ``NonSpineLLMPromptRequest`` -- explicit, primitive-shaped prompt-request package
    built by the runtime from a request (carries the memory-context package);
  - ``NonSpineLLMCompletionAdapter`` -- the completion-boundary base (no provider here);
  - ``FakeNonSpineLLMCompletionAdapter`` -- a deterministic, in-memory, no-provider fake
    that returns a ``NonSpineLLMCompletion``;
  - ``NonSpineLLMCompletion`` -- explicit fake completion result;
  - ``NonSpineLLMRuntime`` -- the owner; ``run(...)`` builds a prompt request (via the
    bounded memory-context package), passes it to the fake adapter's ``complete(...)``,
    and returns a ``NonSpineLLMRuntimeResult``.

Fake path only (by construction):
  - stdlib-only; deterministic; no network; no SDK; no real model call;
  - not on the live Spine path; references no Spine, cognition, or role surface;
  - no retrieval; no assembly; no memory side effects; no persistence; no log output;
  - no endpoint, no MCP registration, no startup hook, no background loop;
  - inert at import time (no import-time side effects).

Live integration is a SEPARATE, separately-authorized gate and is not done here.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple


# Fixed prompt label for the read-only memory-context block.
_MEMORY_CONTEXT_LABEL = "MEMORY-CONTEXT (read-only guidance):"
# Hard cap on rendered memory-context characters.
_MEMORY_CONTEXT_MAX_CHARS = 1200


@dataclass(frozen=True)
class NonSpineLLMMemoryContext:
    """Explicit, bounded, read-only memory-context package (primitive fields only).

    Built from caller-supplied text via :meth:`from_text`. ``is_governed`` is only a
    caller-supplied assertion marker; in this dormant slice it implies NO retrieval or
    assembly authority. An empty package renders no memory block.
    """

    text: str = ""
    source_label: str = ""
    is_read_only: bool = True
    is_governed: bool = False
    max_chars: int = _MEMORY_CONTEXT_MAX_CHARS
    was_truncated: bool = False

    @classmethod
    def empty(cls) -> "NonSpineLLMMemoryContext":
        """Return an empty / no-context package (renders no memory block)."""
        return cls()

    @classmethod
    def from_text(
        cls,
        text: str,
        source_label: str = "",
        is_governed: bool = False,
        max_chars: int = _MEMORY_CONTEXT_MAX_CHARS,
    ) -> "NonSpineLLMMemoryContext":
        """Build a bounded package from caller text.

        Strips first; empty/whitespace becomes the empty package; non-empty text is
        capped at ``max_chars`` and ``was_truncated`` is True only when capped.
        """
        stripped = (text or "").strip()
        if not stripped:
            return cls.empty()
        was_truncated = len(stripped) > max_chars
        bounded = stripped[:max_chars] if was_truncated else stripped
        return cls(
            text=bounded,
            source_label=source_label,
            is_read_only=True,
            is_governed=bool(is_governed),
            max_chars=max_chars,
            was_truncated=was_truncated,
        )

    def is_empty(self) -> bool:
        """True when there is no memory text (renders no memory block)."""
        return not self.text


@dataclass(frozen=True)
class NonSpineLLMRuntimeRequest:
    """Explicit, primitive-only input object for the dormant runtime skeleton.

    Every field is a plain string or a tuple of strings. No repo object dependency.
    """

    agent_id: str = ""
    user_input: str = ""
    system_text: str = ""
    memory_context_text: str = ""
    extra_messages: Tuple[str, ...] = ()


@dataclass(frozen=True)
class NonSpineLLMPromptRequest:
    """Explicit, primitive-shaped prompt-request package built by the runtime.

    Holds the rendered, prompt-shaped data in memory plus the bounded memory-context
    package (for tests). Strings, a string tuple, and the memory-context package only.
    """

    system_text: str = ""
    rendered_prompt: str = ""
    messages: Tuple[str, ...] = ()
    memory_context: "NonSpineLLMMemoryContext" = NonSpineLLMMemoryContext.empty()


@dataclass(frozen=True)
class NonSpineLLMCompletion:
    """Explicit fake completion result returned by the fake adapter.

    ``is_fake`` and ``provider_called`` make the dormant posture explicit and assertable.
    No model produced ``text``; ``echoed_prompt`` is the in-memory request capture for
    tests only.
    """

    text: str
    is_fake: bool
    provider_called: bool
    echoed_prompt: str


@dataclass(frozen=True)
class NonSpineLLMRuntimeResult:
    """Explicit, fake / no-op result object.

    Carries the fake completion data (``completion``) and the captured prompt request
    (``prompt_request`` / ``rendered_prompt``) for tests only; nothing here is emitted
    anywhere.
    """

    response_text: str
    is_fake: bool
    provider_called: bool
    rendered_prompt: str
    completion: "NonSpineLLMCompletion"
    prompt_request: "NonSpineLLMPromptRequest"


# Fixed, recognizable fake response. No model produced this string.
_FAKE_RESPONSE_TEXT = "[non_spine_llm_runtime: dormant fake no-op result]"


class NonSpineLLMCompletionAdapter:
    """Completion-boundary base. Defines the seam; carries no provider.

    A real, separately-authorized adapter would later sit behind this same boundary. The
    base itself performs no completion and contacts no model.
    """

    def complete(
        self, prompt_request: "NonSpineLLMPromptRequest"
    ) -> "NonSpineLLMCompletion":
        raise NotImplementedError


class FakeNonSpineLLMCompletionAdapter(NonSpineLLMCompletionAdapter):
    """Deterministic, in-memory fake completion adapter. No provider, no network.

    ``complete(...)`` returns a fixed-marker ``NonSpineLLMCompletion`` and echoes the
    rendered prompt back for tests. Same input -> same output; no external call.
    """

    def complete(
        self, prompt_request: "NonSpineLLMPromptRequest"
    ) -> "NonSpineLLMCompletion":
        return NonSpineLLMCompletion(
            text=_FAKE_RESPONSE_TEXT,
            is_fake=True,
            provider_called=False,
            echoed_prompt=prompt_request.rendered_prompt,
        )


class NonSpineLLMRuntime:
    """Named internal owner of the dormant, non-Spine LLM runtime skeleton.

    Inert unless a test directly instantiates and calls it. Defaults to the in-memory
    fake completion adapter; holds no resources, opens no connections, imports no
    provider SDK, and touches no repo runtime surface.
    """

    def __init__(self, adapter: "NonSpineLLMCompletionAdapter" = None) -> None:
        # Default to the in-memory fake adapter. No resources, no connections.
        self._adapter: "NonSpineLLMCompletionAdapter" = (
            adapter if adapter is not None else FakeNonSpineLLMCompletionAdapter()
        )

    @staticmethod
    def _build_memory_context(
        request: "NonSpineLLMRuntimeRequest",
        is_governed: bool = True,
        source_label: str = "non_spine_runtime_request",
    ) -> "NonSpineLLMMemoryContext":
        """Build the bounded memory-context package from the request's memory text.

        ``is_governed`` is a caller-supplied assertion marker only -- it confers no
        retrieval or assembly authority in this dormant slice.
        """
        return NonSpineLLMMemoryContext.from_text(
            request.memory_context_text,
            source_label=source_label,
            is_governed=is_governed,
        )

    @staticmethod
    def _render_prompt(
        request: "NonSpineLLMRuntimeRequest",
        memory_context: "NonSpineLLMMemoryContext",
    ) -> str:
        """Render the intended prompt-shaped data into an in-memory string (tests only).

        Pure string composition. The read-only guidance label is included only for a
        non-empty memory-context package; an empty package renders no memory block. It
        performs no external call and produces no durable side effect; the rendered text
        exists only inside the returned objects.
        """
        parts: List[str] = []
        if request.system_text:
            parts.append("SYSTEM: " + request.system_text)
        if not memory_context.is_empty():
            parts.append(_MEMORY_CONTEXT_LABEL + " " + memory_context.text)
        for message in request.extra_messages:
            parts.append("MSG: " + str(message))
        parts.append("USER: " + request.user_input)
        return "\n".join(parts)

    @staticmethod
    def _build_prompt_request(
        request: "NonSpineLLMRuntimeRequest",
    ) -> "NonSpineLLMPromptRequest":
        """Build the prompt-request package using the bounded memory-context package."""
        memory_context = NonSpineLLMRuntime._build_memory_context(request)
        rendered = NonSpineLLMRuntime._render_prompt(request, memory_context)
        return NonSpineLLMPromptRequest(
            system_text=request.system_text,
            rendered_prompt=rendered,
            messages=tuple(request.extra_messages),
            memory_context=memory_context,
        )

    def run(self, request: "NonSpineLLMRuntimeRequest") -> "NonSpineLLMRuntimeResult":
        """Fake, no-provider execution path (test-callable only).

        Builds a prompt request, passes it to the fake completion adapter, and returns a
        fixed no-op result carrying the fake completion and the captured request. No
        model/provider is contacted; nothing is persisted.
        """
        prompt_request = self._build_prompt_request(request)
        completion = self._adapter.complete(prompt_request)
        return NonSpineLLMRuntimeResult(
            response_text=completion.text,
            is_fake=completion.is_fake,
            provider_called=completion.provider_called,
            rendered_prompt=prompt_request.rendered_prompt,
            completion=completion,
            prompt_request=prompt_request,
        )
