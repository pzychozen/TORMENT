"""No-network contract tests for the frozen Meridian Anthropic bridge."""
from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import pytest

from experiments.hivemind_meridian_outage_v1.anthropic_provider import (
    FROZEN_MODEL_ID,
    FrozenAnthropicMeridianProvider,
    HISTORICAL_FAILED_CHARACTERIZATION_ATTEMPT,
    MeridianProviderResponseError,
    SONNET5_CHARACTERIZATION_ROOT,
    SONNET5_CHARACTERIZATION_RUN_IDS,
    load_repo_dotenv_safely,
    parse_meridian_response,
)
from experiments.hivemind_meridian_outage_v1.harness import (
    MeridianOutageHarness,
    NullCoordinationAdapter,
    RESEARCH_INSTRUCTION,
)
from experiments.hivemind_meridian_outage_v1.results import RESULT_SCHEMA_VERSION, verify_sealed_run
from experiments.hivemind_meridian_outage_v1.spec import cards_for_agent, assignment_manifest
from torment_service.non_spine_llm_runtime import (
    NonSpineLLMProviderAdapter,
    NonSpineLLMRealProviderError,
    NonSpineLLMProviderResult,
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


def _provider(texts: Sequence[str] = (_valid_response(),)) -> tuple[FrozenAnthropicMeridianProvider, StubNativeAdapter]:
    native = StubNativeAdapter(texts)
    return FrozenAnthropicMeridianProvider(native_adapter=native), native


def _cards() -> list[dict[str, str]]:
    manifest = assignment_manifest(5)
    return cards_for_agent(manifest, "researcher_001")


def test_sonnet5_model_and_result_schema_are_frozen_for_the_corrected_characterization() -> None:
    assert FROZEN_MODEL_ID == "claude-sonnet-5"
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
    assert bootstrap.credential_configured is True
    assert environment["ANTHROPIC_API_KEY"] == "process-test-secret"
    assert environment["TORMENT_NON_SPINE_LLM_REAL_PROVIDER"] == "1"
    assert environment["MERIDIAN_TEST_VALUE"] == "from-dotenv"
    status_text = json.dumps({
        "dotenv_path": bootstrap.dotenv_path,
        "dotenv_loaded": bootstrap.dotenv_loaded,
        "credential_configured": bootstrap.credential_configured,
    })
    assert "process-test-secret" not in status_text
    assert "dotenv-test-secret" not in status_text


def test_missing_dotenv_and_key_remain_fail_closed_before_sdk_or_network(tmp_path: Path) -> None:
    environment = {"TORMENT_NON_SPINE_LLM_REAL_PROVIDER": "1"}
    provider, bootstrap = FrozenAnthropicMeridianProvider.from_repo_dotenv(
        environment=environment,
        dotenv_path=tmp_path / "missing.env",
    )

    assert bootstrap.dotenv_loaded is False
    assert bootstrap.credential_configured is False
    assert provider.preflight()["credential_configured"] is False
    with pytest.raises(NonSpineLLMRealProviderError, match="ANTHROPIC_API_KEY is not set"):
        provider.run_round(
            agent_id="researcher_001", round_number=1, instruction=RESEARCH_INSTRUCTION,
            assigned_cards=_cards(), collective_context=None, naive_shared_findings=[],
        )


def test_historical_failed_identity_is_preserved_and_sonnet5_identity_is_distinct() -> None:
    assert HISTORICAL_FAILED_CHARACTERIZATION_ATTEMPT["status"] == "FAILED"
    assert "401 invalid x-api-key" in HISTORICAL_FAILED_CHARACTERIZATION_ATTEMPT["cause"]
    assert HISTORICAL_FAILED_CHARACTERIZATION_ATTEMPT["root"] != SONNET5_CHARACTERIZATION_ROOT
    assert len(SONNET5_CHARACTERIZATION_RUN_IDS) == 4
    assert len(set(SONNET5_CHARACTERIZATION_RUN_IDS.values())) == 4
    assert HISTORICAL_FAILED_CHARACTERIZATION_ATTEMPT["run_id"] not in set(
        SONNET5_CHARACTERIZATION_RUN_IDS.values()
    )


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
    assert response.request_metadata["provider_visible_prompt_sha256"]


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


def test_metadata_freezes_exact_configuration_and_contains_no_credentials() -> None:
    provider = FrozenAnthropicMeridianProvider(environment={
        "ANTHROPIC_API_KEY": "metadata-test-secret",
        "TORMENT_NON_SPINE_LLM_REAL_PROVIDER": "1",
    })
    metadata = provider.metadata()
    assert metadata["provider"] == "AnthropicNonSpineLLMProviderAdapter"
    assert metadata["model_id"] == FROZEN_MODEL_ID
    assert metadata["session_isolation"] == "per_agent_per_round"
    assert metadata["retry_policy"] == "none"
    assert metadata["sampling"]["max_tokens"] == {"mode": "explicit", "explicit_value": 1024}
    assert metadata["sampling"]["timeout"] == {"mode": "explicit", "explicit_value": 30}
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
