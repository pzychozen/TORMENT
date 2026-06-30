"""tests/manual/memory_to_prompt_c_d_operator_orchestration_harness.py

Manual / operator harness for the bounded C-D "operator orchestration" direction of the
memory-to-prompt / live-caller lane. The operator hand-orchestrates a single turn: they
supply primitive request fields PLUS a READ-ONLY governed memory-context -- either a literal
fake governed-context string or an injected read-only context callable -- and this harness
composes them into the existing dormant non-Spine runtime request and runs the default
fake / no-provider path.

This is operator-supplied primitives ONLY; it is NOT production wiring. It imports no
production character / store / fabric / retrieval / assembly / orchestrator / runner
surface, touches no app / spine / MCP, performs no retrieval and no assembly (the "governed"
context is operator-supplied read-only input, NOT fetched), changes no retrieval/assembly
behavior, writes no files, persists no transcript/log, ingests / promotes / reinforces no
memory, and routes no model output back into memory. Nothing in production imports it. It
imports only stdlib plus ``torment_service.non_spine_llm_runtime``.

Shape (mirrors the character operator harness):
  - ``MemoryToPromptOperatorHarnessRequest`` -- primitive operator request; carries an
    optional literal ``governed_context_text`` (read-only);
  - ``resolve_operator_memory_context(...)`` -- read-only context resolver: an injected
    ``context_provider`` callable takes precedence (injected read-only context first), else
    the literal governed-context string, else empty;
  - ``build_memory_to_prompt_operator_runtime_request(...)`` -- safe seam: converts the
    primitive request (+ resolved read-only context) into a plain
    ``NonSpineLLMRuntimeRequest`` (persona/system -> system_text; context ->
    memory_context_text);
  - ``run_memory_to_prompt_operator_harness(...)`` -- routes it through the non-Spine
    runtime; default fake / no-provider (``provider_called=False`` / ``is_fake=True``, no
    env, no SDK, no network); an opt-in real path reuses the existing gated
    ``AnthropicNonSpineLLMProviderAdapter``;
  - ``main(...)`` -- argparse CLI; the real path requires ``--real-anthropic`` and refuses
    under pytest before constructing the real adapter; prints only non-secret text.

The real path relies on the adapter's own env gate
(``TORMENT_NON_SPINE_LLM_REAL_PROVIDER=1`` + ``ANTHROPIC_API_KEY`` +
``TORMENT_NON_SPINE_ANTHROPIC_MODEL``) read from the already-activated environment. This
harness does NOT load any dotfile and never prints, stores, echoes, or returns the API key.
Tests exercise the real path with a fake env + fake sdk_factory only.

Run (operator; default fake path needs no env):
    python tests/manual/memory_to_prompt_c_d_operator_orchestration_harness.py \
        --persona-label "Ryuki" --system-text "terse, dry" \
        --governed-context-text "prefers brevity" --user-input "hello"
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from typing import Callable, Optional, Tuple

from torment_service.non_spine_llm_runtime import (
    AnthropicNonSpineLLMProviderAdapter,
    FakeNonSpineLLMCompletionAdapter,
    NonSpineLLMRealProviderError,
    NonSpineLLMRuntime,
    NonSpineLLMRuntimeRequest,
    NonSpineLLMRuntimeResult,
)


@dataclass(frozen=True)
class MemoryToPromptOperatorHarnessRequest:
    """Primitive, operator-supplied request for a single hand-orchestrated turn.

    ``governed_context_text`` is an operator-supplied, READ-ONLY memory-context string. It
    is NOT retrieved or assembled here; the harness treats it as read-only input only.
    """

    agent_id: str = ""
    persona_label: str = ""
    system_text: str = ""
    user_input: str = ""
    governed_context_text: str = ""
    context_source_label: str = "operator_injected_read_only_context"
    extra_messages: Tuple[str, ...] = ()


# An injected, read-only context provider: handed the request, returns a context string.
OperatorContextProvider = Callable[["MemoryToPromptOperatorHarnessRequest"], str]


def _compose_system_text(request: "MemoryToPromptOperatorHarnessRequest") -> str:
    """Compose a plain system_text string from the primitive persona / system fields."""
    parts = []
    if request.persona_label:
        label = request.persona_label
        if request.agent_id:
            label = label + " (" + request.agent_id + ")"
        parts.append("You are " + label + ".")
    elif request.agent_id:
        parts.append("You are " + request.agent_id + ".")
    if request.system_text:
        parts.append(request.system_text)
    return "\n".join(parts)


def resolve_operator_memory_context(
    request: "MemoryToPromptOperatorHarnessRequest",
    context_provider: "Optional[OperatorContextProvider]" = None,
) -> str:
    """Resolve the READ-ONLY governed memory-context string for this turn.

    An injected ``context_provider`` callable takes precedence (use injected read-only
    context first); otherwise the request's literal ``governed_context_text`` is used;
    otherwise empty. The resolved text is treated as read-only input -- nothing is fetched,
    assembled, written, or fed back.
    """
    if context_provider is not None:
        text = context_provider(request)
    else:
        text = request.governed_context_text
    return text or ""


def build_memory_to_prompt_operator_runtime_request(
    request: "MemoryToPromptOperatorHarnessRequest",
    context_provider: "Optional[OperatorContextProvider]" = None,
) -> "NonSpineLLMRuntimeRequest":
    """Safe seam: convert the primitive request (+ read-only context) into a plain runtime
    request.

    The persona / system fields become a composed ``system_text``; the resolved read-only
    governed context becomes ``memory_context_text``. Everything else is forwarded
    primitively. No production surface is touched.
    """
    memory_context_text = resolve_operator_memory_context(
        request, context_provider=context_provider
    )
    return NonSpineLLMRuntimeRequest(
        agent_id=request.agent_id,
        user_input=request.user_input,
        system_text=_compose_system_text(request),
        memory_context_text=memory_context_text,
        extra_messages=tuple(request.extra_messages),
    )


def run_memory_to_prompt_operator_harness(
    request: "MemoryToPromptOperatorHarnessRequest",
    *,
    context_provider: "Optional[OperatorContextProvider]" = None,
    use_real_anthropic: bool = False,
    env=None,
    sdk_factory=None,
) -> "NonSpineLLMRuntimeResult":
    """Orchestrate one turn through the non-Spine runtime; return the result.

    Default (``use_real_anthropic=False``): the runtime's fake completion path
    (``provider_called=False`` / ``is_fake=True``) -- no env, no SDK, no network. Opt-in
    real path wraps the gated ``AnthropicNonSpineLLMProviderAdapter`` (which validates its
    own env gate / key / model and fails closed); ``env`` / ``sdk_factory`` let tests inject
    a fake env + fake SDK so no real env / SDK / network is touched.
    """
    runtime_request = build_memory_to_prompt_operator_runtime_request(
        request, context_provider=context_provider
    )
    if use_real_anthropic:
        provider_adapter = AnthropicNonSpineLLMProviderAdapter(
            env=env, sdk_factory=sdk_factory
        )
        completion_adapter = FakeNonSpineLLMCompletionAdapter(
            provider_adapter=provider_adapter
        )
        runtime = NonSpineLLMRuntime(adapter=completion_adapter)
    else:
        runtime = NonSpineLLMRuntime()
    return runtime.run(runtime_request)


def _pytest_active() -> bool:
    return "pytest" in sys.modules


def main(argv: Optional[list] = None) -> int:
    """Operator CLI. Exit 0 on success; 2 on refused / closed gate / provider failure;
    1 on malformed CLI args or unexpected error. Prints only non-secret text."""
    parser = argparse.ArgumentParser(
        description=(
            "Manual operator-orchestration harness for the memory-to-prompt non-Spine "
            "runtime (read-only governed context in, fake completion out)."
        )
    )
    parser.add_argument("--agent-id", default="")
    parser.add_argument("--persona-label", default="")
    parser.add_argument("--system-text", default="")
    parser.add_argument("--user-input", default="")
    parser.add_argument("--governed-context-text", default="")
    parser.add_argument("--extra-message", action="append", default=[])
    parser.add_argument("--real-anthropic", action="store_true")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return 1 if (exc.code or 0) != 0 else 0

    if args.real_anthropic and _pytest_active():
        # Refuse the real path under pytest BEFORE constructing the real adapter.
        print("refused: pytest detected; will not construct the real provider")
        return 2

    request = MemoryToPromptOperatorHarnessRequest(
        agent_id=args.agent_id,
        persona_label=args.persona_label,
        system_text=args.system_text,
        user_input=args.user_input,
        governed_context_text=args.governed_context_text,
        extra_messages=tuple(args.extra_message),
    )
    try:
        # CLI orchestrates with the literal read-only governed context only (no callable).
        result = run_memory_to_prompt_operator_harness(
            request, use_real_anthropic=args.real_anthropic
        )
    except NonSpineLLMRealProviderError as exc:
        # gate unset / missing key/model / bad timeout / SDK unavailable / provider error /
        # empty or malformed response. The adapter names env-var KEYS only, never values.
        print("refused / closed: %s" % exc)
        return 2
    except Exception:
        print("unexpected harness error")
        return 1

    # Print only the non-secret result text.
    print(result.response_text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
