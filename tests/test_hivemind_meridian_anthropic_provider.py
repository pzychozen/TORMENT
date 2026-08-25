"""No-network contract tests for the frozen Meridian Anthropic bridge."""
from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import pytest

from experiments.hivemind_meridian_outage_v1.anthropic_provider import (
    FROZEN_MAX_TOKENS,
    FROZEN_MODEL_ID,
    FROZEN_TIMEOUT_SECONDS,
    FrozenAnthropicMeridianProvider,
    HISTORICAL_FAILED_CHARACTERIZATION_ATTEMPT,
    HISTORICAL_FAILED_SONNET_EMPTY_TEXT_CHARACTERIZATION_ATTEMPT,
    HISTORICAL_FAILED_SONNET_FREE_FORM_SCHEMA_CHARACTERIZATION_ATTEMPT,
    HISTORICAL_FAILED_SONNET_OUTPUT_BUDGET_CHARACTERIZATION_ATTEMPT,
    HISTORICAL_FAILED_SONNET_CHARACTERIZATION_ATTEMPT,
    HISTORICAL_FAILED_SONNET_SCHEMA_CHARACTERIZATION_ATTEMPT,
    HISTORICAL_FAILED_SONNET_TIMEOUT_CHARACTERIZATION_ATTEMPT,
    MERIDIAN_RESPONSE_JSON_SCHEMA,
    MERIDIAN_RESPONSE_JSON_SCHEMA_ID,
    MERIDIAN_RESPONSE_JSON_SCHEMA_VERSION,
    MERIDIAN_STRUCTURED_OUTPUT_CONFIG,
    MeridianProviderResponseError,
    SONNET5G_STRUCTURED_OUTPUT_SUCCESSOR_CHARACTERIZATION_ROOT,
    SONNET5G_STRUCTURED_OUTPUT_SUCCESSOR_RUN_IDS,
    load_repo_dotenv_safely,
    parse_meridian_response,
)
from experiments.hivemind_meridian_outage_v1.harness import (
    MeridianOutageHarness,
    NullCoordinationAdapter,
    RESEARCH_INSTRUCTION,
)
from experiments.hivemind_meridian_outage_v1.results import RESULT_SCHEMA_VERSION, verify_sealed_run
from experiments.hivemind_meridian_outage_v1.spec import cards_for_agent, assignment_manifest, payload_sha256
from torment_service.non_spine_llm_runtime import (
    AnthropicNonSpineLLMProviderAdapter,
    NonSpineLLMProviderAdapter,
    NonSpineLLMProviderRequest,
    NonSpineLLMRealProviderError,
    NonSpineLLMProviderResult,
    NonSpineLLMPromptRequest,
)


def _valid_response(*, card_id: str = "D-001") -> str:
    return json.dumps({
        "findings": [{"text": "Evidence is uncertain.", "card_ids": [card_id], "share_permitted": True}],
        "claims": [{"text": "A poison interpretation is refuted.", "card_ids": [card_id], "stance": "refutes"}],
        "final_answer": {
            "root_cause": "Clock drift requires investigation.",
            "contributing_factors": ["certificate timing"],
            "cited_card_ids": [card_id],
        },
        "collective_context_consumed": False,
    }, ensure_ascii=False, separators=(",", ":"))


class StubNativeAdapter(NonSpineLLMProviderAdapter):
    def __init__(self, texts: Sequence[str]) -> None:
        self.texts = list(texts)
        self.requests: list[Any] = []

    def generate(self, request: Any) -> NonSpineLLMProviderResult:
        self.requests.append(request)
        return NonSpineLLMProviderResult(
            text=self.texts.pop(0),
            is_fake=False,
            provider_called=True,
            provider_name="anthropic",
            model_name=FROZEN_MODEL_ID,
            echoed_prompt=request.prompt_request.rendered_prompt,
        )


class PromptAwareNativeAdapter(NonSpineLLMProviderAdapter):
    def __init__(self) -> None:
        self.requests: list[Any] = []

    def generate(self, request: Any) -> NonSpineLLMProviderResult:
        self.requests.append(request)
        _, payload_text = request.prompt_request.rendered_prompt.split("\n", 1)
        payload = json.loads(payload_text)
        card_id = payload["assigned_cards"][0]["card_id"]
        return NonSpineLLMProviderResult(
            text=_valid_response(card_id=card_id),
            is_fake=False,
            provider_called=True,
            provider_name="anthropic",
            model_name=FROZEN_MODEL_ID,
            echoed_prompt=request.prompt_request.rendered_prompt,
        )


class _TextBlock:
    def __init__(self, text: str) -> None:
        self.text = text


class _Message:
    def __init__(self, text: str) -> None:
        self.content = [_TextBlock(text)]
        self.stop_reason = "end_turn"


def _matches_json_schema(value: object, schema: Mapping[str, Any]) -> bool:
    schema_type = schema.get("type")
    if schema_type == "object":
        if not isinstance(value, dict):
            return False
        properties = schema.get("properties")
        required = schema.get("required")
        if not isinstance(properties, Mapping) or not isinstance(required, list):
            return False
        if any(key not in value for key in required):
            return False
        if schema.get("additionalProperties") is False and set(value) - set(properties):
            return False
        return all(
            key in properties
            and isinstance(properties[key], Mapping)
            and _matches_json_schema(item, properties[key])
            for key, item in value.items()
        )
    if schema_type == "array":
        items = schema.get("items")
        return isinstance(value, list) and isinstance(items, Mapping) and all(
            _matches_json_schema(item, items) for item in value
        )
    if schema_type == "string":
        if not isinstance(value, str) or len(value) < schema.get("minLength", 0):
            return False
        enum = schema.get("enum")
        return not isinstance(enum, list) or value in enum
    return schema_type == "boolean" and type(value) is bool


class _StructuredOutputSdkFactory:
    """Fake normal Messages API that rejects output invalid under its supplied schema."""

    def __init__(self, response_text: str) -> None:
        self.response_text = response_text
        self.create_kwargs: dict[str, Any] | None = None

    def __call__(self):
        factory = self

        class _Messages:
            def create(self, **kwargs):
                factory.create_kwargs = kwargs
                output_config = kwargs.get("output_config")
                if not isinstance(output_config, Mapping):
                    raise RuntimeError("structured output config is absent")
                format_config = output_config.get("format")
                if not isinstance(format_config, Mapping) or format_config.get("type") != "json_schema":
                    raise RuntimeError("structured output format is malformed")
                schema = format_config.get("schema")
                if not isinstance(schema, Mapping) or not _matches_json_schema(
                    json.loads(factory.response_text), schema,
                ):
                    raise RuntimeError("mock structured output rejected the response")
                return _Message(factory.response_text)

        class _Client:
            def __init__(self, **_kwargs) -> None:
                self.messages = _Messages()

        class _Module:
            Anthropic = _Client

        return _Module


def _native_structured_adapter(factory: _StructuredOutputSdkFactory) -> AnthropicNonSpineLLMProviderAdapter:
    return AnthropicNonSpineLLMProviderAdapter(
        env={
            "ANTHROPIC_API_KEY": "fake-key",
            "TORMENT_NON_SPINE_LLM_REAL_PROVIDER": "1",
            "TORMENT_NON_SPINE_ANTHROPIC_MODEL": FROZEN_MODEL_ID,
        },
        sdk_factory=factory,
        max_tokens=FROZEN_MAX_TOKENS,
        timeout_seconds=FROZEN_TIMEOUT_SECONDS,
        output_config=MERIDIAN_STRUCTURED_OUTPUT_CONFIG,
    )


def _native_structured_request() -> NonSpineLLMProviderRequest:
    return NonSpineLLMProviderRequest(
        prompt_request=NonSpineLLMPromptRequest(
            rendered_prompt="fake Meridian prompt", system_text=RESEARCH_INSTRUCTION,
        ),
    )


def _provider(texts: Sequence[str] = (_valid_response(),)) -> tuple[FrozenAnthropicMeridianProvider, StubNativeAdapter]:
    native = StubNativeAdapter(texts)
    return FrozenAnthropicMeridianProvider(native_adapter=native), native


def _cards() -> list[dict[str, str]]:
    manifest = assignment_manifest(5)
    return cards_for_agent(manifest, "researcher_001")


def test_sonnet5_model_and_result_schema_are_frozen_for_the_corrected_characterization() -> None:
    assert FROZEN_MODEL_ID == "claude-sonnet-5"
    assert FROZEN_MAX_TOKENS == 16_000
    assert FROZEN_TIMEOUT_SECONDS == 600
    assert RESULT_SCHEMA_VERSION == "meridian-result-v2"


def test_repo_dotenv_bootstrap_is_redacted_and_process_environment_takes_precedence(tmp_path: Path) -> None:
    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text(
        "ANTHROPIC_API_KEY=dotenv-test-secret\n"
        "TORMENT_NON_SPINE_LLM_REAL_PROVIDER=0\n"
        "MERIDIAN_TEST_VALUE=from-dotenv\n",
        encoding="utf-8",
    )
    environment = {
        "ANTHROPIC_API_KEY": "process-test-secret",
        "TORMENT_NON_SPINE_LLM_REAL_PROVIDER": "1",
    }

    bootstrap = load_repo_dotenv_safely(environment=environment, dotenv_path=dotenv_path)

    assert bootstrap.dotenv_path == str(dotenv_path.resolve())
    assert bootstrap.dotenv_loaded is True
    assert bootstrap.dotenv_read_error is False
    assert bootstrap.credential_configured is True
    assert bootstrap.credential_source == "process_environment"
    assert environment["ANTHROPIC_API_KEY"] == "process-test-secret"
    assert environment["TORMENT_NON_SPINE_LLM_REAL_PROVIDER"] == "1"
    assert environment["MERIDIAN_TEST_VALUE"] == "from-dotenv"
    status_text = json.dumps({
        "dotenv_path": bootstrap.dotenv_path,
        "dotenv_loaded": bootstrap.dotenv_loaded,
        "dotenv_read_error": bootstrap.dotenv_read_error,
        "credential_configured": bootstrap.credential_configured,
        "credential_source": bootstrap.credential_source,
    })
    assert "process-test-secret" not in status_text
    assert "dotenv-test-secret" not in status_text
    assert "process-test-secret" not in repr(bootstrap)
    assert "dotenv-test-secret" not in repr(bootstrap)


def test_repo_dotenv_populates_an_absent_credential_with_redacted_provenance(tmp_path: Path) -> None:
    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text("ANTHROPIC_API_KEY=dotenv-test-secret\n", encoding="utf-8")
    environment: dict[str, str] = {}

    provider, bootstrap = FrozenAnthropicMeridianProvider.from_repo_dotenv(
        environment=environment,
        dotenv_path=dotenv_path,
    )

    assert bootstrap.dotenv_loaded is True
    assert bootstrap.dotenv_read_error is False
    assert bootstrap.credential_configured is True
    assert bootstrap.credential_source == "repo_dotenv"
    assert environment["ANTHROPIC_API_KEY"] == "dotenv-test-secret"
    assert "dotenv-test-secret" not in repr(bootstrap)
    assert provider.preflight()["network_contact_performed"] is False


def test_missing_dotenv_and_key_remain_fail_closed_before_sdk_or_network(tmp_path: Path) -> None:
    environment = {"TORMENT_NON_SPINE_LLM_REAL_PROVIDER": "1"}
    provider, bootstrap = FrozenAnthropicMeridianProvider.from_repo_dotenv(
        environment=environment,
        dotenv_path=tmp_path / "missing.env",
    )

    assert bootstrap.dotenv_loaded is False
    assert bootstrap.dotenv_read_error is False
    assert bootstrap.credential_configured is False
    assert bootstrap.credential_source == "absent"
    assert provider.preflight()["credential_configured"] is False
    with pytest.raises(NonSpineLLMRealProviderError, match="ANTHROPIC_API_KEY is not set"):
        provider.run_round(
            agent_id="researcher_001", round_number=1, instruction=RESEARCH_INSTRUCTION,
            assigned_cards=_cards(), collective_context=None, naive_shared_findings=[],
        )


def test_unreadable_repo_dotenv_is_redacted_and_remains_fail_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text("ANTHROPIC_API_KEY=dotenv-unreadable-test-secret\n", encoding="utf-8")

    def _raise_permission_error(*args: object, **kwargs: object) -> object:
        raise PermissionError("test-only unreadable dotenv")

    monkeypatch.setattr("builtins.open", _raise_permission_error)
    bootstrap = load_repo_dotenv_safely(environment={}, dotenv_path=dotenv_path)

    assert bootstrap.dotenv_loaded is False
    assert bootstrap.dotenv_read_error is True
    assert bootstrap.credential_configured is False
    assert bootstrap.credential_source == "absent"
    assert "dotenv-unreadable-test-secret" not in repr(bootstrap)


def test_failed_sonnet_identities_are_closed_and_successor_identity_is_distinct() -> None:
    assert HISTORICAL_FAILED_CHARACTERIZATION_ATTEMPT["status"] == "FAILED"
    assert "401 invalid x-api-key" in HISTORICAL_FAILED_CHARACTERIZATION_ATTEMPT["cause"]
    assert HISTORICAL_FAILED_SONNET_CHARACTERIZATION_ATTEMPT == {
        "root": r"C:\TORMENT\m5s5",
        "condition": "A_PRIVATE",
        "logical_call": "round_1:researcher_001",
        "model_id": "claude-sonnet-5",
        "attempted_provider_calls": 1,
        "succeeded_provider_calls": 0,
        "failed_provider_calls": 1,
        "retry_count": 0,
        "status": "FAILED",
        "scientific_interpretation": "AUTHENTICATION / CONFIGURATION FAILURE",
        "cause": "Anthropic 401 authentication_error / invalid x-api-key",
    }
    assert HISTORICAL_FAILED_SONNET_EMPTY_TEXT_CHARACTERIZATION_ATTEMPT == {
        "root": r"C:\TORMENT\m5s5b",
        "run_id": "meridian-n5-sonnet5b-20260824-a-private",
        "condition": "A_PRIVATE",
        "logical_call": "round_1:researcher_001",
        "model_id": "claude-sonnet-5",
        "attempted_provider_calls": 1,
        "succeeded_provider_calls": 0,
        "failed_provider_calls": 1,
        "retry_count": 0,
        "status": "FAILED",
        "scientific_interpretation": "UNRESOLVED PROVIDER BEHAVIOR",
        "cause": "anthropic returned empty or malformed text",
    }
    assert (
        HISTORICAL_FAILED_SONNET_OUTPUT_BUDGET_CHARACTERIZATION_ATTEMPT
        == {
            "root": r"C:\TORMENT\m5s5c",
            "run_id": "meridian-n5-sonnet5c-20260824-a-private",
            "condition": "A_PRIVATE",
            "logical_call": "round_1:researcher_001",
            "model_id": "claude-sonnet-5",
            "max_tokens": 1024,
            "attempted_provider_calls": 1,
            "succeeded_provider_calls": 0,
            "failed_provider_calls": 1,
            "retry_count": 0,
            "status": "FAILED",
            "scientific_interpretation": "OUTPUT-BUDGET EXHAUSTION",
            "cause": "ThinkingBlock only; no TextBlock; stop_reason=max_tokens",
        }
    )
    assert (
        HISTORICAL_FAILED_SONNET_TIMEOUT_CHARACTERIZATION_ATTEMPT
        == {
            "root": r"C:\TORMENT\m5s5d",
            "run_id": "meridian-n5-sonnet5d-20260824-a-private",
            "condition": "A_PRIVATE",
            "logical_call": "round_1:researcher_001",
            "model_id": "claude-sonnet-5",
            "max_tokens": 16_000,
            "timeout_seconds": 30,
            "attempted_provider_calls": 1,
            "succeeded_provider_calls": 0,
            "failed_provider_calls": 1,
            "retry_count": 0,
            "status": "FAILED",
            "scientific_interpretation": "TIMEOUT",
            "cause": "Request timed out or interrupted",
        }
    )
    assert (
        HISTORICAL_FAILED_SONNET_TIMEOUT_CHARACTERIZATION_ATTEMPT["root"]
        != HISTORICAL_FAILED_SONNET_SCHEMA_CHARACTERIZATION_ATTEMPT["root"]
    )
    assert HISTORICAL_FAILED_SONNET_SCHEMA_CHARACTERIZATION_ATTEMPT == {
        "root": r"C:\TORMENT\m5s5e",
        "run_id": "meridian-n5-sonnet5e-20260824-a-private",
        "condition": "A_PRIVATE",
        "logical_call": "round_2:researcher_005",
        "model_id": "claude-sonnet-5",
        "max_tokens": 16_000,
        "timeout_seconds": 600,
        "attempted_provider_calls": 10,
        "succeeded_provider_calls": 9,
        "failed_provider_calls": 1,
        "retry_count": 0,
        "status": "FAILED",
        "scientific_interpretation": "MODEL OUTPUT CONTRACT NONCOMPLIANCE — MINOR EXTRA-FIELD DEVIATION",
        "cause": "finding index 1 had forbidden extra stance_note field",
    }
    assert (
        HISTORICAL_FAILED_SONNET_SCHEMA_CHARACTERIZATION_ATTEMPT["root"]
        != HISTORICAL_FAILED_SONNET_FREE_FORM_SCHEMA_CHARACTERIZATION_ATTEMPT["root"]
    )
    assert HISTORICAL_FAILED_SONNET_FREE_FORM_SCHEMA_CHARACTERIZATION_ATTEMPT == {
        "root": r"C:\TORMENT\m5s5f",
        "run_id": "meridian-n5-sonnet5f-20260824-a-private",
        "condition": "A_PRIVATE",
        "logical_call": "round_2:researcher_002",
        "model_id": "claude-sonnet-5",
        "max_tokens": 16_000,
        "timeout_seconds": 600,
        "attempted_provider_calls": 7,
        "succeeded_provider_calls": 6,
        "failed_provider_calls": 1,
        "unexecuted_provider_calls": 3,
        "retry_count": 0,
        "status": "FAILED",
        "scientific_interpretation": "FREE-FORM OUTPUT-SCHEMA NONCOMPLIANCE",
        "cause": "finding has an unexpected structure",
    }
    assert (
        HISTORICAL_FAILED_SONNET_FREE_FORM_SCHEMA_CHARACTERIZATION_ATTEMPT["root"]
        != SONNET5G_STRUCTURED_OUTPUT_SUCCESSOR_CHARACTERIZATION_ROOT
    )
    assert len(SONNET5G_STRUCTURED_OUTPUT_SUCCESSOR_RUN_IDS) == 4
    assert len(set(SONNET5G_STRUCTURED_OUTPUT_SUCCESSOR_RUN_IDS.values())) == 4
    assert set(SONNET5G_STRUCTURED_OUTPUT_SUCCESSOR_RUN_IDS.values()) == {
        "meridian-n5-sonnet5g-20260825-a-private",
        "meridian-n5-sonnet5g-20260825-b1-mechanisms-only",
        "meridian-n5-sonnet5g-20260825-b2-salience-surfaced",
        "meridian-n5-sonnet5g-20260825-c-naive-shared-content",
    }


def test_valid_json_uses_native_public_seam_and_preserves_raw_text_exactly() -> None:
    provider, native = _provider()
    response = provider.run_round(
        agent_id="researcher_001", round_number=1, instruction=RESEARCH_INSTRUCTION,
        assigned_cards=_cards(), collective_context=None, naive_shared_findings=[],
    )
    assert response.raw_response_text == _valid_response()
    assert response.output["claims"][0]["stance"] == "refutes"
    assert native.requests[0].config.model_name == FROZEN_MODEL_ID
    assert native.requests[0].config.network_enabled is True
    assert response.request_metadata["provider_visible_prompt_sha256"] == payload_sha256({
        "system_instruction": RESEARCH_INSTRUCTION,
        "rendered_prompt": native.requests[0].prompt_request.rendered_prompt,
    })


def test_parser_accepts_a_valid_frozen_response_without_repair() -> None:
    assert parse_meridian_response(_valid_response()) == json.loads(_valid_response())


@pytest.mark.parametrize("raw", (
    "not json",
    "```json\n{}\n```",
    json.dumps({"findings": [], "claims": [], "final_answer": {}, "collective_context_consumed": False}),
    json.dumps({"findings": "wrong", "claims": [], "final_answer": {}, "collective_context_consumed": False}),
    json.dumps({
        "findings": [],
        "claims": [{"text": "x", "card_ids": ["D-001"], "stance": "invalid"}],
        "final_answer": {"root_cause": "x", "contributing_factors": [], "cited_card_ids": ["D-001"]},
        "collective_context_consumed": False,
    }),
    json.dumps({
        "findings": [{"text": "x", "card_ids": ["not-a-card"], "share_permitted": True}],
        "claims": [],
        "final_answer": {"root_cause": "x", "contributing_factors": [], "cited_card_ids": ["D-001"]},
        "collective_context_consumed": False,
    }),
))
def test_parser_rejects_invalid_or_non_exact_responses(raw: str) -> None:
    with pytest.raises(MeridianProviderResponseError):
        parse_meridian_response(raw)


def test_parser_rejects_unknown_top_level_keys_and_missing_citations() -> None:
    unknown = json.loads(_valid_response())
    unknown["extra"] = "not frozen"
    with pytest.raises(MeridianProviderResponseError):
        parse_meridian_response(json.dumps(unknown))
    missing_citations = json.loads(_valid_response())
    del missing_citations["final_answer"]["cited_card_ids"]
    with pytest.raises(MeridianProviderResponseError):
        parse_meridian_response(json.dumps(missing_citations))


def test_parser_rejects_extra_finding_keys_without_repair() -> None:
    extra_field = json.loads(_valid_response())
    extra_field["findings"][0]["stance_note"] = "not in the frozen schema"

    with pytest.raises(MeridianProviderResponseError, match="finding has an unexpected structure"):
        parse_meridian_response(json.dumps(extra_field))


def test_native_structured_output_schema_accepts_the_valid_frozen_response() -> None:
    raw_response = _valid_response()
    factory = _StructuredOutputSdkFactory(raw_response)

    result = _native_structured_adapter(factory).generate(_native_structured_request())

    assert result.text == raw_response
    assert factory.create_kwargs is not None
    assert factory.create_kwargs["output_config"] == MERIDIAN_STRUCTURED_OUTPUT_CONFIG


@pytest.mark.parametrize("mutate", (
    lambda response: response["findings"][0].update({"stance_note": "forbidden"}),
    lambda response: response["findings"][0].pop("share_permitted"),
    lambda response: response["findings"][0].update({"share_permitted": "wrong type"}),
))
def test_native_structured_output_schema_rejects_extra_missing_and_wrong_type_fields(mutate: Any) -> None:
    response = json.loads(_valid_response())
    mutate(response)
    factory = _StructuredOutputSdkFactory(json.dumps(response))

    with pytest.raises(NonSpineLLMRealProviderError, match="mock structured output rejected"):
        _native_structured_adapter(factory).generate(_native_structured_request())

    assert factory.create_kwargs is not None
    assert factory.create_kwargs["output_config"] == MERIDIAN_STRUCTURED_OUTPUT_CONFIG


def test_metadata_freezes_exact_configuration_and_contains_no_credentials() -> None:
    provider = FrozenAnthropicMeridianProvider(environment={
        "ANTHROPIC_API_KEY": "metadata-test-secret",
        "TORMENT_NON_SPINE_LLM_REAL_PROVIDER": "1",
    })
    metadata = provider.metadata()
    assert metadata["provider"] == "AnthropicNonSpineLLMProviderAdapter"
    assert metadata["model_id"] == FROZEN_MODEL_ID
    assert provider._native_adapter._max_tokens == FROZEN_MAX_TOKENS
    assert provider._native_adapter._timeout_seconds == FROZEN_TIMEOUT_SECONDS
    assert provider._native_adapter._output_config == MERIDIAN_STRUCTURED_OUTPUT_CONFIG
    assert metadata["session_isolation"] == "per_agent_per_round"
    assert metadata["retry_policy"] == "none"
    assert metadata["structured_output"] is True
    assert metadata["structured_output_schema"] == {
        "id": MERIDIAN_RESPONSE_JSON_SCHEMA_ID,
        "version": MERIDIAN_RESPONSE_JSON_SCHEMA_VERSION,
        "sha256": payload_sha256(MERIDIAN_RESPONSE_JSON_SCHEMA),
    }
    assert metadata["sampling"]["max_tokens"] == {
        "mode": "explicit", "explicit_value": FROZEN_MAX_TOKENS,
    }
    assert metadata["sampling"]["timeout"] == {
        "mode": "explicit", "explicit_value": FROZEN_TIMEOUT_SECONDS,
    }
    for field in ("temperature", "top_p", "top_k", "thinking"):
        assert metadata["sampling"][field] == {"mode": "provider_default", "explicit_value": None}
    assert "key" not in json.dumps(metadata).lower()
    assert "metadata-test-secret" not in json.dumps(metadata)


def test_prompt_rendering_is_deterministic_and_does_not_expose_condition_names() -> None:
    cards = list(reversed(_cards()))
    first = FrozenAnthropicMeridianProvider.render_prompt(
        agent_id="researcher_001", round_number=2, instruction=RESEARCH_INSTRUCTION,
        assigned_cards=cards, collective_context=None, naive_shared_findings=[],
    )
    second = FrozenAnthropicMeridianProvider.render_prompt(
        agent_id="researcher_001", round_number=2, instruction=RESEARCH_INSTRUCTION,
        assigned_cards=list(reversed(cards)), collective_context=None, naive_shared_findings=[],
    )
    assert first == second
    assert "A_PRIVATE" not in first and "B1_TORMENT" not in first and "B2_TORMENT" not in first
    assert "C_NAIVE" not in first
    instruction, payload = first.split("\n", 1)
    assert instruction == (
        "Return exactly one JSON object matching the native structured-output schema. "
        "Do not use markdown fences or add prose before or after the object."
    )
    assert "response_schema" not in json.loads(payload)


def test_prompt_condition_boundaries_only_change_permitted_additions() -> None:
    common = {
        "agent_id": "researcher_001", "round_number": 2, "instruction": RESEARCH_INSTRUCTION,
        "assigned_cards": _cards(),
    }
    private = FrozenAnthropicMeridianProvider.render_prompt(
        **common, collective_context=None, naive_shared_findings=[],
    )
    b1 = FrozenAnthropicMeridianProvider.render_prompt(
        **common, collective_context=None, naive_shared_findings=[],
    )
    b2 = FrozenAnthropicMeridianProvider.render_prompt(
        **common, collective_context={"recent_events": [{"event_id": "cev_1"}], "event_count": 1},
        naive_shared_findings=[],
    )
    naive = FrozenAnthropicMeridianProvider.render_prompt(
        **common, collective_context=None,
        naive_shared_findings=[{"agent_id": "researcher_002", "text": "peer finding", "card_ids": ["D-002"]}],
    )
    assert private == b1
    assert '"collective_context"' not in private and '"naive_shared_findings"' not in private
    assert '"collective_context"' in b2 and '"naive_shared_findings"' not in b2
    assert '"naive_shared_findings"' in naive and '"collective_context"' not in naive
    assert "peer finding" not in b2


def test_bridge_has_no_hidden_transcript_or_retry_state() -> None:
    provider, native = _provider((_valid_response(), _valid_response()))
    kwargs = {
        "agent_id": "researcher_001", "round_number": 1, "instruction": RESEARCH_INSTRUCTION,
        "assigned_cards": _cards(), "collective_context": None, "naive_shared_findings": [],
    }
    first = provider.run_round(**kwargs)
    second = provider.run_round(**{**kwargs, "agent_id": "researcher_002", "round_number": 2})
    assert len(native.requests) == 2
    assert first.raw_response_text not in native.requests[1].prompt_request.rendered_prompt
    assert second.raw_response_text not in native.requests[0].prompt_request.rendered_prompt


def test_invalid_bridge_response_seals_failed_meridian_evidence_without_retry(tmp_path: Path) -> None:
    provider, native = _provider(("invalid live response",))
    run_dir = MeridianOutageHarness(provider, NullCoordinationAdapter()).run(
        output_root=tmp_path, run_id="bridge-invalid", condition="A_PRIVATE", n_agents=5,
    )
    result = verify_sealed_run(run_dir)
    raw = json.loads((run_dir / "raw_outputs.json").read_text(encoding="utf-8"))
    assert result["run_status"] == "FAILED"
    assert result["model_call_evidence"]["logical_model_call_count_attempted"] == 1
    assert len(native.requests) == 1
    assert raw["provider_attempts"][0]["raw_response_text"] == "invalid live response"
    assert raw["provider_attempts"][0]["parser_schema_outcome"] == "failed"


def test_bridge_is_an_interchangeable_complete_meridian_provider(tmp_path: Path) -> None:
    native = PromptAwareNativeAdapter()
    run_dir = MeridianOutageHarness(
        FrozenAnthropicMeridianProvider(native_adapter=native), NullCoordinationAdapter(),
    ).run(output_root=tmp_path, run_id="bridge-complete", condition="A_PRIVATE", n_agents=5)
    result = verify_sealed_run(run_dir, require_complete=True)
    raw = json.loads((run_dir / "raw_outputs.json").read_text(encoding="utf-8"))
    assert result["provider"]["model_id"] == FROZEN_MODEL_ID
    assert len(native.requests) == 10
    assert all(
        attempt["request_metadata"]["provider_visible_prompt_sha256"]
        for attempt in raw["provider_attempts"]
    )


def test_preflight_uses_presence_only_for_credentials_and_never_contacts_provider() -> None:
    class NoCredentialReadEnvironment(dict[str, str]):
        def get(self, key: str, default: Any = None) -> Any:
            raise AssertionError("preflight must not read environment values")

    environment = NoCredentialReadEnvironment({"ANTHROPIC_API_KEY": "unused", "TORMENT_NON_SPINE_LLM_REAL_PROVIDER": "1"})
    provider = FrozenAnthropicMeridianProvider(environment=environment)
    preflight = provider.preflight()
    assert preflight["credential_configured"] is True
    assert preflight["real_provider_gate_configured"] is True
    assert preflight["adapter_construction_possible"] is True
    assert preflight["network_contact_performed"] is False
