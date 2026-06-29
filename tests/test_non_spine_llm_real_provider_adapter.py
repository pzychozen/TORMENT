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


class _FakeResponse:
    def __init__(self, blocks):
        self.content = blocks


class _SpySdkFactory:
    def __init__(self, blocks=None, raises_on_create=None):
        self.called = 0
        self.blocks = blocks if blocks is not None else [_FakeBlock("hi from fake")]
        self.raises_on_create = raises_on_create
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
                return _FakeResponse(factory.blocks)

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


class TestAnthropicAdapterIsNotDefault(unittest.TestCase):
    def test_default_runtime_remains_fake(self):
        res = NonSpineLLMRuntime().run(NonSpineLLMRuntimeRequest(user_input="hi"))
        self.assertIs(res.is_fake, True)
        self.assertIs(res.provider_called, False)
        self.assertIn("fake no-op", res.response_text)


if __name__ == "__main__":
    unittest.main()
