"""torment_service/non_spine_llm_runtime.py

Dormant, internal, NON-Spine LLM runtime SKELETON.

This module is the named owner shape selected ON PAPER by the separate-LLM-runtime
direction-selection frame (docs-only). Its default / fake / callable paths are INERT and
production-unwired; nothing in production instantiates or calls them.

Shape:
  - ``NonSpineLLMMemoryContext`` -- explicit, bounded, read-only memory-context package;
  - ``NonSpineLLMRuntimeRequest`` -- explicit, primitive-only input object;
  - ``NonSpineLLMPromptRequest`` -- explicit prompt-request package (carries memory ctx);
  - ``NonSpineLLMProviderConfig`` / ``NonSpineLLMProviderRequest`` /
    ``NonSpineLLMProviderResult`` -- provider-adapter readiness contracts;
  - ``NonSpineLLMProviderAdapter`` -- the provider boundary base (no provider);
  - ``FakeNonSpineLLMProviderAdapter`` -- a deterministic, in-memory, no-provider fake;
  - a callable-only MANUAL provider adapter (operator-injected callable; never default);
  - ``AnthropicNonSpineLLMProviderAdapter`` -- the first REAL provider adapter (gated,
    lazy-import, fail-closed, operator-constructed only; never the default and never
    live-wired);
  - ``NonSpineLLMCompletionAdapter`` / ``FakeNonSpineLLMCompletionAdapter`` -- the only
    default completion path; delegates through the fake provider adapter;
  - ``NonSpineLLMCompletion`` -- explicit fake completion result;
  - ``NonSpineLLMRuntime`` -- the owner; ``run(...)`` stays fake / no-provider;
  - ``run_non_spine_callable_provider_manual(...)`` -- production-internal MANUAL helper.

Default / fake / callable paths (by construction):
  - stdlib-only at import; deterministic; the default runtime, the fake adapters, and the
    callable adapter make no network, SDK, env, or secret access and no real call;
  - not on the live Spine path; references no Spine, cognition, or role surface;
  - no retrieval; no assembly; no memory side effects; no persistence; no log output;
  - no endpoint, no MCP registration, no startup hook, no background loop;
  - inert at import time (no import-time side effects).

The ONE exception is ``AnthropicNonSpineLLMProviderAdapter`` -- the first REAL provider
adapter: operator-constructed only, never the default and never live-wired, gated by an env
var, with the ``anthropic`` SDK lazily imported only AFTER the gate / key / model are
validated, an explicit timeout (default <= 30s), and fail-closed behavior. Importing this
module and constructing the adapter still do nothing (no env read, no SDK import); a real
call happens only when an operator constructs it, the gate is set, and generate() runs.

Live integration is a SEPARATE, separately-authorized gate and is not done here.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Tuple


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
class NonSpineLLMProviderConfig:
    """Fake, network-disabled provider configuration (primitive fields only)."""

    provider_name: str = "fake"
    model_name: str = "fake-non-spine"
    is_fake: bool = True
    network_enabled: bool = False


@dataclass(frozen=True)
class NonSpineLLMProviderRequest:
    """Provider-adapter request: carries the prompt-request package and the config."""

    prompt_request: "NonSpineLLMPromptRequest"
    config: "NonSpineLLMProviderConfig" = NonSpineLLMProviderConfig()


@dataclass(frozen=True)
class NonSpineLLMProviderResult:
    """Explicit provider result (primitive fields only).

    For the fake adapter ``is_fake`` is True / ``provider_called`` is False. For the
    callable or real adapter these may be False / True respectively.
    """

    text: str
    is_fake: bool
    provider_called: bool
    provider_name: str
    model_name: str
    echoed_prompt: str


@dataclass(frozen=True)
class NonSpineLLMCompletion:
    """Explicit fake completion result returned by the fake completion adapter."""

    text: str
    is_fake: bool
    provider_called: bool
    echoed_prompt: str


@dataclass(frozen=True)
class NonSpineLLMRuntimeResult:
    """Explicit, fake / no-op result object (default runtime path)."""

    response_text: str
    is_fake: bool
    provider_called: bool
    rendered_prompt: str
    completion: "NonSpineLLMCompletion"
    prompt_request: "NonSpineLLMPromptRequest"


# Fixed, recognizable fake response. No model produced this string.
_FAKE_RESPONSE_TEXT = "[non_spine_llm_runtime: dormant fake no-op result]"


class NonSpineLLMProviderAdapter:
    """Provider-adapter boundary base. Defines the seam; the base contacts no model."""

    def generate(
        self, request: "NonSpineLLMProviderRequest"
    ) -> "NonSpineLLMProviderResult":
        raise NotImplementedError


class FakeNonSpineLLMProviderAdapter(NonSpineLLMProviderAdapter):
    """Deterministic, in-memory fake provider adapter. No network, no SDK, no env."""

    def generate(
        self, request: "NonSpineLLMProviderRequest"
    ) -> "NonSpineLLMProviderResult":
        config = request.config
        return NonSpineLLMProviderResult(
            text=_FAKE_RESPONSE_TEXT,
            is_fake=True,
            provider_called=False,
            provider_name=config.provider_name,
            model_name=config.model_name,
            echoed_prompt=request.prompt_request.rendered_prompt,
        )


class CallableNonSpineLLMProviderAdapter(NonSpineLLMProviderAdapter):
    """Callable-only MANUAL provider adapter.

    NOT a real SDK adapter, NOT env-gated, NOT network-enabled, and NEVER the default
    runtime path -- the base runtime never instantiates it. It requires an operator-
    injected callable handed the ``NonSpineLLMProviderRequest`` and returning a string.
    This is one place where ``provider_called`` may be True and ``is_fake`` may be False;
    tests use only fake / spy callables. It imports no SDK, reaches no network, no env.
    """

    def __init__(
        self,
        completion_callable: "Callable[[NonSpineLLMProviderRequest], str]",
    ) -> None:
        if not callable(completion_callable):
            raise TypeError("completion_callable must be callable")
        self._completion_callable = completion_callable

    def generate(
        self, request: "NonSpineLLMProviderRequest"
    ) -> "NonSpineLLMProviderResult":
        text = self._completion_callable(request)
        config = request.config
        return NonSpineLLMProviderResult(
            text=str(text),
            is_fake=False,
            provider_called=True,
            provider_name=config.provider_name,
            model_name=config.model_name,
            echoed_prompt=request.prompt_request.rendered_prompt,
        )


class NonSpineLLMCompletionAdapter:
    """Completion-boundary base. Defines the seam; the base contacts no model."""

    def complete(
        self, prompt_request: "NonSpineLLMPromptRequest"
    ) -> "NonSpineLLMCompletion":
        raise NotImplementedError


class FakeNonSpineLLMCompletionAdapter(NonSpineLLMCompletionAdapter):
    """The only default completion path. Deterministic and no-provider by default.

    ``complete(...)`` builds a ``NonSpineLLMProviderRequest`` and delegates through its
    provider adapter's ``generate(...)``, then converts the result into a
    ``NonSpineLLMCompletion``. The default provider adapter is the in-memory fake; an
    operator MAY inject a different provider adapter explicitly.
    """

    def __init__(
        self, provider_adapter: "NonSpineLLMProviderAdapter" = None
    ) -> None:
        # Default to the in-memory fake provider adapter. No resources, no connections.
        self._provider_adapter: "NonSpineLLMProviderAdapter" = (
            provider_adapter
            if provider_adapter is not None
            else FakeNonSpineLLMProviderAdapter()
        )

    def complete(
        self, prompt_request: "NonSpineLLMPromptRequest"
    ) -> "NonSpineLLMCompletion":
        provider_request = NonSpineLLMProviderRequest(
            prompt_request=prompt_request,
            config=NonSpineLLMProviderConfig(),
        )
        provider_result = self._provider_adapter.generate(provider_request)
        return NonSpineLLMCompletion(
            text=provider_result.text,
            is_fake=provider_result.is_fake,
            provider_called=provider_result.provider_called,
            echoed_prompt=provider_result.echoed_prompt,
        )


class NonSpineLLMRuntime:
    """Named internal owner of the dormant, non-Spine LLM runtime skeleton.

    Defaults to the in-memory fake completion adapter; holds no resources, opens no
    connections, imports no provider SDK, and touches no repo runtime surface.
    """

    def __init__(self, adapter: "NonSpineLLMCompletionAdapter" = None) -> None:
        # Default to the in-memory fake completion adapter. No resources, no connections.
        self._adapter: "NonSpineLLMCompletionAdapter" = (
            adapter if adapter is not None else FakeNonSpineLLMCompletionAdapter()
        )

    @staticmethod
    def _build_memory_context(
        request: "NonSpineLLMRuntimeRequest",
        is_governed: bool = True,
        source_label: str = "non_spine_runtime_request",
    ) -> "NonSpineLLMMemoryContext":
        """Build the bounded memory-context package from the request's memory text."""
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
        non-empty memory-context package; an empty package renders no memory block.
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
        fixed no-op result. No model/provider is contacted; nothing is persisted.
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


def run_non_spine_callable_provider_manual(
    completion_callable: "Callable",
    *,
    agent_id: str = "",
    user_input: str = "",
    system_text: str = "",
    memory_context_text: str = "",
    extra_messages: Tuple[str, ...] = (),
) -> "NonSpineLLMRuntimeResult":
    """Production-internal MANUAL helper: build the callable-adapter stack and run a turn.

    NOT live-wired and NOT the default path -- nothing in production calls it.
    """
    request = NonSpineLLMRuntimeRequest(
        agent_id=agent_id,
        user_input=user_input,
        system_text=system_text,
        memory_context_text=memory_context_text,
        extra_messages=tuple(extra_messages),
    )
    callable_adapter = CallableNonSpineLLMProviderAdapter(completion_callable)
    completion_adapter = FakeNonSpineLLMCompletionAdapter(
        provider_adapter=callable_adapter
    )
    runtime = NonSpineLLMRuntime(adapter=completion_adapter)
    return runtime.run(request)


class NonSpineLLMRealProviderError(RuntimeError):
    """Raised when the real-provider adapter refuses (fail-closed) or a call fails.

    Used by ``AnthropicNonSpineLLMProviderAdapter`` for: gate unset, missing API key,
    missing model, bad timeout, SDK unavailable, provider exception, or empty / malformed
    response. There is no fallback provider and no retry.
    """


class AnthropicNonSpineLLMProviderAdapter(NonSpineLLMProviderAdapter):
    """First REAL provider adapter for the non-Spine runtime (Anthropic).

    Operator-constructed ONLY; never the default, never instantiated by
    ``NonSpineLLMRuntime`` or ``FakeNonSpineLLMCompletionAdapter`` defaults, never
    live-wired. Gated, lazy-import, and fail-closed:

      - it refuses (raises ``NonSpineLLMRealProviderError``) BEFORE importing the SDK or
        contacting a provider unless the env gate is exactly "1" and the API key and model
        are present;
      - the ``anthropic`` SDK is imported LAZILY, only after that validation;
      - the call uses an explicit timeout (default <= 30s);
      - on gate-unset, missing key/model, bad timeout, SDK unavailable, provider exception,
        or empty / malformed response it fails closed with a clear exception;
      - no fallback provider, no retry, no ranking, no style steering, no fake-as-real
        substitution, no persistence, no log output, and no memory side effect or
        model-output-to-memory feedback.

    For testability the constructor accepts an optional explicit ``env`` mapping and an
    optional ``sdk_factory`` (a zero-arg callable returning an ``anthropic``-shaped module);
    when omitted, ``env`` resolves to ``os.environ`` and the SDK is the lazily-imported
    ``anthropic`` package. Automated tests inject a fake env and a fake / monkeypatched SDK
    only -- they never reach a real provider. No env lookup happens at construction.
    """

    PROVIDER_NAME = "anthropic"
    GATE_ENV = "TORMENT_NON_SPINE_LLM_REAL_PROVIDER"
    API_KEY_ENV = "ANTHROPIC_API_KEY"
    MODEL_ENV = "TORMENT_NON_SPINE_ANTHROPIC_MODEL"
    TIMEOUT_ENV = "TORMENT_NON_SPINE_PROVIDER_TIMEOUT_SECONDS"
    DEFAULT_TIMEOUT_SECONDS = 30
    MAX_TOKENS = 1024
    _SAFE_STOP_REASONS = frozenset({
        "end_turn",
        "max_tokens",
        "stop_sequence",
        "tool_use",
        "pause_turn",
        "refusal",
        "model_context_window_exceeded",
    })

    def __init__(self, env=None, sdk_factory=None, max_tokens: int | None = None) -> None:
        # Store readers only. No env lookup, no SDK import, no provider contact here.
        if max_tokens is not None and (type(max_tokens) is not int or max_tokens <= 0):
            raise ValueError("max_tokens must be a positive integer")
        self._env = env
        self._sdk_factory = sdk_factory
        self._max_tokens = self.MAX_TOKENS if max_tokens is None else max_tokens

    def _resolve_env(self):
        if self._env is not None:
            return self._env
        import os  # stdlib; resolved here at call time, never at module import
        return os.environ

    def _require_gate(self, env) -> None:
        if env.get(self.GATE_ENV) != "1":
            raise NonSpineLLMRealProviderError(
                "real-provider gate %s is not set to '1'" % self.GATE_ENV
            )

    def _require_value(self, env, key: str) -> str:
        value = (env.get(key) or "").strip()
        if not value:
            raise NonSpineLLMRealProviderError("%s is not set" % key)
        return value

    def _parse_timeout(self, env) -> float:
        raw = (env.get(self.TIMEOUT_ENV) or "").strip()
        if not raw:
            return float(self.DEFAULT_TIMEOUT_SECONDS)
        try:
            seconds = float(raw)
        except (TypeError, ValueError):
            raise NonSpineLLMRealProviderError("%s must be a number" % self.TIMEOUT_ENV)
        if seconds <= 0 or seconds > self.DEFAULT_TIMEOUT_SECONDS:
            raise NonSpineLLMRealProviderError(
                "%s must be in (0, %d] seconds"
                % (self.TIMEOUT_ENV, self.DEFAULT_TIMEOUT_SECONDS)
            )
        return seconds

    def _load_sdk(self):
        try:
            if self._sdk_factory is not None:
                return self._sdk_factory()
            import anthropic  # lazy: imported ONLY after gate / key / model validation
            return anthropic
        except NonSpineLLMRealProviderError:
            raise
        except Exception as exc:
            raise NonSpineLLMRealProviderError(
                "anthropic SDK could not be loaded: %s" % exc
            )

    @staticmethod
    def _extract_text(response) -> str:
        text, _ = AnthropicNonSpineLLMProviderAdapter._extract_text_with_shape(response)
        return text

    @staticmethod
    def _extract_text_with_shape(response) -> tuple[str, dict[str, object]]:
        """Extract only text blocks and retain safe shape diagnostics for failures."""
        stop_reason_value = getattr(response, "stop_reason", None)
        stop_reason = (
            stop_reason_value
            if isinstance(stop_reason_value, str)
            and stop_reason_value in AnthropicNonSpineLLMProviderAdapter._SAFE_STOP_REASONS
            else "unrecognized" if isinstance(stop_reason_value, str) else None
        )
        shape: dict[str, object] = {
            "response_type": type(response).__name__,
            "content_block_count": 0,
            "content_block_types": [],
            "text_field_block_count": 0,
            "stop_reason": stop_reason if isinstance(stop_reason, str) else None,
        }
        content = getattr(response, "content", None)
        if not content:
            return "", shape
        parts = []
        try:
            for block in content:
                shape["content_block_count"] = int(shape["content_block_count"]) + 1
                block_types = shape["content_block_types"]
                if isinstance(block_types, list):
                    block_types.append(type(block).__name__)
                value = getattr(block, "text", None)
                if isinstance(value, str):
                    shape["text_field_block_count"] = int(shape["text_field_block_count"]) + 1
                    parts.append(value)
        except TypeError:
            return "", shape
        return "".join(parts).strip(), shape

    @staticmethod
    def _empty_response_error(shape: dict[str, object]) -> NonSpineLLMRealProviderError:
        """Return a fail-closed error containing structural, never textual, response data."""
        block_types = shape["content_block_types"]
        block_types_text = ",".join(block_types) if isinstance(block_types, list) and block_types else "none"
        stop_reason = shape["stop_reason"] or "none"
        return NonSpineLLMRealProviderError(
            "anthropic returned empty or malformed text "
            "(response_type=%s, content_block_count=%d, content_block_types=%s, "
            "text_field_block_count=%d, stop_reason=%s)"
            % (
                shape["response_type"],
                shape["content_block_count"],
                block_types_text,
                shape["text_field_block_count"],
                stop_reason,
            )
        )

    def generate(
        self, request: "NonSpineLLMProviderRequest"
    ) -> "NonSpineLLMProviderResult":
        env = self._resolve_env()
        self._require_gate(env)                              # refuse before SDK import
        api_key = self._require_value(env, self.API_KEY_ENV)  # refuse before SDK import
        model = self._require_value(env, self.MODEL_ENV)      # refuse before SDK import
        timeout = self._parse_timeout(env)
        sdk = self._load_sdk()                               # lazy import AFTER validation
        try:
            client = sdk.Anthropic(api_key=api_key, timeout=timeout)
            response = client.messages.create(
                model=model,
                max_tokens=self._max_tokens,
                system=request.prompt_request.system_text or "",
                messages=[
                    {"role": "user", "content": request.prompt_request.rendered_prompt}
                ],
            )
        except NonSpineLLMRealProviderError:
            raise
        except Exception as exc:
            raise NonSpineLLMRealProviderError(
                "anthropic provider call failed: %s" % exc
            )
        text, response_shape = self._extract_text_with_shape(response)
        if not text:
            raise self._empty_response_error(response_shape)
        return NonSpineLLMProviderResult(
            text=text,
            is_fake=False,
            provider_called=True,
            provider_name=self.PROVIDER_NAME,
            model_name=model,
            echoed_prompt=request.prompt_request.rendered_prompt,
        )
