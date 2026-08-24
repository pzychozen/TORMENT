"""tests/test_non_spine_llm_real_provider_adapter.py

Guards for the first REAL provider adapter (Anthropic). Every test uses a FAKE env mapping
plus a FAKE / spy SDK factory only -- no real env lookup, no SDK install, no network, no
real provider call.
"""
import unittest

from torment_service.non_spine_llm_runtime import (
    NonSpineLLMProviderAdapter,
    NonSpineLLMProviderRequest,
    NonSpineLLMProviderResult,
    NonSpineLLMPromptRequest,
    NonSpineLLMRuntime,
    NonSpineLLMRuntimeRequest,
    AnthropicNonSpineLLMProviderAdapter,
    NonSpineLLMRealProviderError,
)

GATE = "TORMENT_NON_SPINE_LLM_REAL_PROVIDER"
KEY = "ANTHROPIC_API_KEY"
MODEL = "TORMENT_NON_SPINE_ANTHROPIC_MODEL"
TIMEOUT = "TORMENT_NON_SPINE_PROVIDER_TIMEOUT_SECONDS"


def _valid_env(**over):
    env = {GATE: "1", KEY: "sk-fake", MODEL: "claude-fake"}
    env.update(over)
    return env


def _req(rendered="USER: hi", system="sys"):
    return NonSpineLLMProviderRequest(
        prompt_request=NonSpineLLMPromptRequest(rendered_prompt=rendered, system_text=system))


class _FakeBlock:
    def __init__(self, text):
        self.text = text


class _FakeThinkingBlock:
    def __init__(self, thinking):
        self.thinking = thinking


class _FakeRedactedThinkingBlock:
    def __init__(self, data):
        self.data = data


class _FakeToolUseBlock:
    def __init__(self, tool_input):
        self.input = tool_input


class _FakeResponse:
    def __init__(self, blocks, stop_reason=None):
        self.content = blocks
        self.stop_reason = stop_reason


class _SpySdkFactory:
    def __init__(self, blocks=None, raises_on_create=None, stop_reason=None):
        self.called = 0
        self.blocks = blocks if blocks is not None else [_FakeBlock("hi from fake")]
        self.raises_on_create = raises_on_create
        self.stop_reason = stop_reason
        self.client = None

    def __call__(self):
        self.called += 1
        factory = self

        class _Messages:
            def __init__(self):
                self.create_kwargs = None

            def create(self, **kwargs):
                self.create_kwargs = kwargs
                if factory.raises_on_create is not None:
                    raise factory.raises_on_create
                return _FakeResponse(factory.blocks, stop_reason=factory.stop_reason)

        class _Client:
            def __init__(self, **kwargs):
                self.init_kwargs = kwargs
                self.messages = _Messages()
                factory.client = self

        class _Module:
            Anthropic = _Client

        return _Module


class TestAnthropicAdapterShape(unittest.TestCase):
    def test_exists_and_subclass(self):
        self.assertIsInstance(AnthropicNonSpineLLMProviderAdapter, type)
        self.assertTrue(issubclass(AnthropicNonSpineLLMProviderAdapter, NonSpineLLMProviderAdapter))

    def test_no_env_lookup_at_construction(self):
        spy = _SpySdkFactory()
        AnthropicNonSpineLLMProviderAdapter(env={}, sdk_factory=spy)
        self.assertEqual(spy.called, 0)


class TestAnthropicAdapterRefusal(unittest.TestCase):
    def _adapter(self, env, spy):
        return AnthropicNonSpineLLMProviderAdapter(env=env, sdk_factory=spy)

    def test_gate_unset_refuses_before_sdk(self):
        spy = _SpySdkFactory()
        with self.assertRaises(NonSpineLLMRealProviderError):
            self._adapter({}, spy).generate(_req())
        self.assertEqual(spy.called, 0)

    def test_gate_wrong_value_refuses(self):
        spy = _SpySdkFactory()
        with self.assertRaises(NonSpineLLMRealProviderError):
            self._adapter({GATE: "0", KEY: "k", MODEL: "m"}, spy).generate(_req())
        self.assertEqual(spy.called, 0)

    def test_missing_key_refuses_before_sdk(self):
        spy = _SpySdkFactory()
        with self.assertRaises(NonSpineLLMRealProviderError):
            self._adapter({GATE: "1", MODEL: "m"}, spy).generate(_req())
        self.assertEqual(spy.called, 0)

    def test_missing_model_refuses_before_sdk(self):
        spy = _SpySdkFactory()
        with self.assertRaises(NonSpineLLMRealProviderError):
            self._adapter({GATE: "1", KEY: "k"}, spy).generate(_req())
        self.assertEqual(spy.called, 0)


class TestAnthropicAdapterSdkAndTimeout(unittest.TestCase):
    def test_sdk_loaded_only_after_validation(self):
        spy = _SpySdkFactory()
        AnthropicNonSpineLLMProviderAdapter(env=_valid_env(), sdk_factory=spy).generate(_req())
        self.assertEqual(spy.called, 1)

    def test_sdk_missing_fails_closed(self):
        def _raises():
            raise ImportError("anthropic not installed")
        with self.assertRaises(NonSpineLLMRealProviderError):
            AnthropicNonSpineLLMProviderAdapter(env=_valid_env(), sdk_factory=_raises).generate(_req())

    def test_default_timeout_at_most_30(self):
        self.assertLessEqual(AnthropicNonSpineLLMProviderAdapter.DEFAULT_TIMEOUT_SECONDS, 30)

    def test_timeout_env_parses_and_passed(self):
        spy = _SpySdkFactory()
        AnthropicNonSpineLLMProviderAdapter(env=_valid_env(**{TIMEOUT: "10"}), sdk_factory=spy).generate(_req())
        self.assertEqual(spy.client.init_kwargs.get("timeout"), 10.0)

    def test_default_timeout_when_unset(self):
        spy = _SpySdkFactory()
        AnthropicNonSpineLLMProviderAdapter(env=_valid_env(), sdk_factory=spy).generate(_req())
        self.assertEqual(spy.client.init_kwargs.get("timeout"), 30.0)

    def test_bad_timeout_fails_closed(self):
        for bad in ("abc", "0", "-5", "31"):
            spy = _SpySdkFactory()
            with self.assertRaises(NonSpineLLMRealProviderError):
                AnthropicNonSpineLLMProviderAdapter(env=_valid_env(**{TIMEOUT: bad}), sdk_factory=spy).generate(_req())
            self.assertEqual(spy.called, 0)


class TestAnthropicAdapterCall(unittest.TestCase):
    def test_provider_exception_fails_closed(self):
        spy = _SpySdkFactory(raises_on_create=RuntimeError("boom"))
        with self.assertRaises(NonSpineLLMRealProviderError):
            AnthropicNonSpineLLMProviderAdapter(env=_valid_env(), sdk_factory=spy).generate(_req())

    def test_empty_or_malformed_response_fails_closed(self):
        for blocks in ([], [_FakeBlock("")], [object()]):
            spy = _SpySdkFactory(blocks=blocks)
            with self.assertRaises(NonSpineLLMRealProviderError):
                AnthropicNonSpineLLMProviderAdapter(env=_valid_env(), sdk_factory=spy).generate(_req())

    def test_thinking_block_followed_by_text_block_extracts_only_final_text(self):
        spy = _SpySdkFactory(
            blocks=[_FakeThinkingBlock("private-thinking"), _FakeBlock("visible answer")],
            stop_reason="end_turn",
        )
        result = AnthropicNonSpineLLMProviderAdapter(env=_valid_env(), sdk_factory=spy).generate(_req())
        self.assertEqual(result.text, "visible answer")

    def test_non_text_blocks_fail_closed_with_safe_structural_diagnostics(self):
        cases = (
            (_FakeThinkingBlock("private-thinking"), "_FakeThinkingBlock", "private-thinking"),
            (_FakeRedactedThinkingBlock("private-redacted-data"), "_FakeRedactedThinkingBlock", "private-redacted-data"),
            (_FakeToolUseBlock({"private": "tool-input"}), "_FakeToolUseBlock", "tool-input"),
        )
        for block, expected_type, forbidden_text in cases:
            with self.subTest(block_type=expected_type):
                spy = _SpySdkFactory(blocks=[block], stop_reason="max_tokens")
                with self.assertRaises(NonSpineLLMRealProviderError) as raised:
                    AnthropicNonSpineLLMProviderAdapter(env=_valid_env(), sdk_factory=spy).generate(_req())
                message = str(raised.exception)
                self.assertIn("content_block_count=1", message)
                self.assertIn("content_block_types=" + expected_type, message)
                self.assertIn("text_field_block_count=0", message)
                self.assertIn("stop_reason=max_tokens", message)
                self.assertNotIn(forbidden_text, message)

    def test_empty_text_block_diagnostic_reports_shape_without_text_content(self):
        spy = _SpySdkFactory(blocks=[_FakeBlock("")], stop_reason="end_turn")
        with self.assertRaises(NonSpineLLMRealProviderError) as raised:
            AnthropicNonSpineLLMProviderAdapter(env=_valid_env(), sdk_factory=spy).generate(_req())
        message = str(raised.exception)
        self.assertIn("content_block_types=_FakeBlock", message)
        self.assertIn("text_field_block_count=1", message)
        self.assertIn("stop_reason=end_turn", message)

    def test_unrecognized_stop_reason_is_not_exposed(self):
        spy = _SpySdkFactory(blocks=[], stop_reason="private-stop-reason")
        with self.assertRaises(NonSpineLLMRealProviderError) as raised:
            AnthropicNonSpineLLMProviderAdapter(env=_valid_env(), sdk_factory=spy).generate(_req())
        message = str(raised.exception)
        self.assertIn("stop_reason=unrecognized", message)
        self.assertNotIn("private-stop-reason", message)

    def test_success_with_fake_module_no_network(self):
        spy = _SpySdkFactory(blocks=[_FakeBlock("hello from anthropic-fake")])
        res = AnthropicNonSpineLLMProviderAdapter(env=_valid_env(), sdk_factory=spy).generate(_req("USER: hi", "sys"))
        self.assertIsInstance(res, NonSpineLLMProviderResult)
        self.assertIs(res.is_fake, False)
        self.assertIs(res.provider_called, True)
        self.assertEqual(res.provider_name, "anthropic")
        self.assertEqual(res.model_name, "claude-fake")
        self.assertEqual(res.text, "hello from anthropic-fake")
        self.assertEqual(res.echoed_prompt, "USER: hi")

    def test_success_passes_rendered_prompt_as_user_message(self):
        spy = _SpySdkFactory()
        AnthropicNonSpineLLMProviderAdapter(env=_valid_env(), sdk_factory=spy).generate(_req("USER: where to?", "you are x"))
        kwargs = spy.client.messages.create_kwargs
        self.assertEqual(kwargs["messages"][0]["content"], "USER: where to?")
        self.assertEqual(kwargs["system"], "you are x")
        self.assertEqual(kwargs["model"], "claude-fake")
        self.assertEqual(kwargs["max_tokens"], AnthropicNonSpineLLMProviderAdapter.MAX_TOKENS)

    def test_explicit_max_tokens_overrides_the_generic_default(self):
        spy = _SpySdkFactory()
        AnthropicNonSpineLLMProviderAdapter(
            env=_valid_env(), sdk_factory=spy, max_tokens=16_000,
        ).generate(_req())
        self.assertEqual(spy.client.messages.create_kwargs["max_tokens"], 16_000)


class TestAnthropicAdapterIsNotDefault(unittest.TestCase):
    def test_default_runtime_remains_fake(self):
        res = NonSpineLLMRuntime().run(NonSpineLLMRuntimeRequest(user_input="hi"))
        self.assertIs(res.is_fake, True)
        self.assertIs(res.provider_called, False)
        self.assertIn("fake no-op", res.response_text)


if __name__ == "__main__":
    unittest.main()
