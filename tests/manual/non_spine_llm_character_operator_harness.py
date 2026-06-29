"""tests/manual/non_spine_llm_character_operator_harness.py

Manual / operator harness that builds a CHARACTER-SHAPED request from operator-provided
primitive fields and routes it into the existing dormant non-Spine runtime. "Character-
shaped" here means primitive operator-supplied fields ONLY (character_id / character_name /
seed_text / user_input / memory_context_text / extra_messages) -- it is NOT production
character integration: it imports no production character / store / fabric / assembly /
orchestrator / runner surface, touches no app / spine /
MCP, writes no files, persists no transcript/log, and ingests no memory.

Shape:
  - ``NonSpineLLMCharacterHarnessRequest`` -- primitive operator request;
  - ``build_non_spine_character_runtime_request(...)`` -- safe seam: converts the
    character-shaped request into a plain ``NonSpineLLMRuntimeRequest`` (the character
    fields become a composed ``system_text``);
  - ``run_non_spine_character_operator_harness(...)`` -- runs it through the non-Spine
    runtime; default fake / no-provider (``provider_called=False`` / ``is_fake=True``,
    no env, no SDK, no network); an opt-in real path reuses the existing gated
    ``AnthropicNonSpineLLMProviderAdapter``;
  - ``main(...)`` -- argparse CLI; the real path requires ``--real-anthropic`` and refuses
    under pytest before constructing the real adapter; prints only non-secret text.

The real path relies on the adapter's own env gate
(``TORMENT_NON_SPINE_LLM_REAL_PROVIDER=1`` + ``ANTHROPIC_API_KEY`` +
``TORMENT_NON_SPINE_ANTHROPIC_MODEL``) read from the already-activated environment. This
harness does NOT load ``.env`` and never prints, stores, echoes, or returns the API key.
Tests exercise the real path with a fake env + fake sdk_factory only.

Run (operator; default fake path needs no env):
    python tests/manual/non_spine_llm_character_operator_harness.py \
        --character-name "Ryuki" --seed-text "terse, dry" --user-input "hello"
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from typing import Optional, Tuple

from torment_service.non_spine_llm_runtime import (
    AnthropicNonSpineLLMProviderAdapter,
    FakeNonSpineLLMCompletionAdapter,
    NonSpineLLMRealProviderError,
    NonSpineLLMRuntime,
    NonSpineLLMRuntimeRequest,
    NonSpineLLMRuntimeResult,
)


@dataclass(frozen=True)
class NonSpineLLMCharacterHarnessRequest:
    """Primitive, operator-supplied character-shaped request (no production character)."""

    character_id: str = ""
    character_name: str = ""
    seed_text: str = ""
    user_input: str = ""
    memory_context_text: str = ""
    extra_messages: Tuple[str, ...] = ()


def _compose_system_text(request: "NonSpineLLMCharacterHarnessRequest") -> str:
    """Compose a plain system_text string from the primitive character fields."""
    parts = []
    if request.character_name:
        label = request.character_name
        if request.character_id:
            label = label + " (" + request.character_id + ")"
        parts.append("You are " + label + ".")
    elif request.character_id:
        parts.append("You are " + request.character_id + ".")
    if request.seed_text:
        parts.append(request.seed_text)
    return "\n".join(parts)


def build_non_spine_character_runtime_request(
    request: "NonSpineLLMCharacterHarnessRequest",
) -> "NonSpineLLMRuntimeRequest":
    """Safe seam: convert the character-shaped request into a plain runtime request.

    The character fields become a composed ``system_text``; everything else is forwarded
    primitively. No production character surface is touched.
    """
    return NonSpineLLMRuntimeRequest(
        agent_id=request.character_id,
        user_input=request.user_input,
        system_text=_compose_system_text(request),
        memory_context_text=request.memory_context_text,
        extra_messages=tuple(request.extra_messages),
    )


def run_non_spine_character_operator_harness(
    request: "NonSpineLLMCharacterHarnessRequest",
    *,
    use_real_anthropic: bool = False,
    env=None,
    sdk_factory=None,
) -> "NonSpineLLMRuntimeResult":
    """Route a character-shaped request through the non-Spine runtime; return the result.

    Default (``use_real_anthropic=False``): the runtime's fake completion path
    (``provider_called=False`` / ``is_fake=True``) -- no env, no SDK, no network. Opt-in
    real path wraps the gated ``AnthropicNonSpineLLMProviderAdapter`` (which validates its
    own env gate / key / model and fails closed); ``env`` / ``sdk_factory`` let tests inject
    a fake env + fake SDK so no real env / SDK / network is touched.
    """
    runtime_request = build_non_spine_character_runtime_request(request)
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
        description="Manual character-shaped operator harness for the non-Spine runtime."
    )
    parser.add_argument("--character-id", default="")
    parser.add_argument("--character-name", default="")
    parser.add_argument("--seed-text", default="")
    parser.add_argument("--user-input", default="")
    parser.add_argument("--memory-context-text", default="")
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

    request = NonSpineLLMCharacterHarnessRequest(
        character_id=args.character_id,
        character_name=args.character_name,
        seed_text=args.seed_text,
        user_input=args.user_input,
        memory_context_text=args.memory_context_text,
        extra_messages=tuple(args.extra_message),
    )
    try:
        result = run_non_spine_character_operator_harness(
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
