"""torment_service/non_spine_llm_runtime.py

Dormant, internal, NON-Spine LLM runtime SKELETON (test-callable only).

This module is the named owner shape selected ON PAPER by the separate-LLM-runtime
direction-selection frame (docs-only). It is INERT: nothing in production instantiates
or calls it. It exists so a future, separately-authorized step has a concrete, fenced
skeleton to build against.

Shape:
  - ``NonSpineLLMRuntimeRequest`` -- explicit, primitive-only input object;
  - ``NonSpineLLMPromptRequest`` -- explicit, primitive-shaped prompt-request package
    built by the runtime from a request;
  - ``NonSpineLLMCompletionAdapter`` -- the completion-boundary base (no provider here);
  - ``FakeNonSpineLLMCompletionAdapter`` -- a deterministic, in-memory, no-provider fake
    that returns a ``NonSpineLLMCompletion``;
  - ``NonSpineLLMCompletion`` -- explicit fake completion result;
  - ``NonSpineLLMRuntime`` -- the owner; ``run(...)`` builds a prompt request, passes it
    to the fake adapter's ``complete(...)``, and returns a ``NonSpineLLMRuntimeResult``.

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

    Holds the rendered, prompt-shaped data in memory for the fake adapter and for tests.
    Strings and a string tuple only; no repo object dependency.
    """

    system_text: str = ""
    rendered_prompt: str = ""
    messages: Tuple[str, ...] = ()


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
    def _render_prompt(request: "NonSpineLLMRuntimeRequest") -> str:
        """Render the intended prompt-shaped data into an in-memory string (tests only).

        Pure string composition. It performs no external call and produces no durable
        side effect; the rendered text exists only inside the returned objects.
        """
        parts: List[str] = []
        if request.system_text:
            parts.append("SYSTEM: " + request.system_text)
        if request.memory_context_text:
            parts.append(
                "MEMORY-CONTEXT (read-only guidance): " + request.memory_context_text
            )
        for message in request.extra_messages:
            parts.append("MSG: " + str(message))
        parts.append("USER: " + request.user_input)
        return "\n".join(parts)

    @staticmethod
    def _build_prompt_request(
        request: "NonSpineLLMRuntimeRequest",
    ) -> "NonSpineLLMPromptRequest":
        """Build the explicit prompt-request package from a primitive input request."""
        rendered = NonSpineLLMRuntime._render_prompt(request)
        return NonSpineLLMPromptRequest(
            system_text=request.system_text,
            rendered_prompt=rendered,
            messages=tuple(request.extra_messages),
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
