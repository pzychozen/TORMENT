"""Frozen Anthropic bridge for Meridian Outage v1 only.

Construction and preflight are inert: the native provider is contacted only if
``run_round`` is called after its own gate and credential checks succeed.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import os
import re
from collections.abc import Mapping, MutableMapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any

from torment_service.non_spine_llm_runtime import (
    AnthropicNonSpineLLMProviderAdapter,
    NonSpineLLMProviderAdapter,
    NonSpineLLMProviderConfig,
    NonSpineLLMProviderRequest,
    NonSpineLLMPromptRequest,
)

from .harness import ProviderRoundResponse, RESEARCH_INSTRUCTION
from .spec import CARD_IDS, payload_sha256


FROZEN_MODEL_ID = "claude-sonnet-5"
FROZEN_MAX_TOKENS = 16_000
FROZEN_TIMEOUT_SECONDS = 600
REPO_ROOT = Path(__file__).resolve().parents[2]
REPO_DOTENV_PATH = REPO_ROOT / ".env"
HISTORICAL_FAILED_CHARACTERIZATION_ATTEMPT = MappingProxyType({
    "root": r"C:\TORMENT\meridian_outage_v1_n5_characterization_20260824",
    "run_id": "meridian-n5-characterization-20260824-a-private",
    "status": "FAILED",
    "cause": "operator-session credential rejected by Anthropic with 401 invalid x-api-key",
})
HISTORICAL_FAILED_SONNET_CHARACTERIZATION_ATTEMPT = MappingProxyType({
    "root": r"C:\TORMENT\m5s5",
    "condition": "A_PRIVATE",
    "logical_call": "round_1:researcher_001",
    "model_id": FROZEN_MODEL_ID,
    "attempted_provider_calls": 1,
    "succeeded_provider_calls": 0,
    "failed_provider_calls": 1,
    "retry_count": 0,
    "status": "FAILED",
    "scientific_interpretation": "AUTHENTICATION / CONFIGURATION FAILURE",
    "cause": "Anthropic 401 authentication_error / invalid x-api-key",
})
HISTORICAL_FAILED_SONNET_EMPTY_TEXT_CHARACTERIZATION_ATTEMPT = MappingProxyType({
    "root": r"C:\TORMENT\m5s5b",
    "run_id": "meridian-n5-sonnet5b-20260824-a-private",
    "condition": "A_PRIVATE",
    "logical_call": "round_1:researcher_001",
    "model_id": FROZEN_MODEL_ID,
    "attempted_provider_calls": 1,
    "succeeded_provider_calls": 0,
    "failed_provider_calls": 1,
    "retry_count": 0,
    "status": "FAILED",
    "scientific_interpretation": "UNRESOLVED PROVIDER BEHAVIOR",
    "cause": "anthropic returned empty or malformed text",
})
HISTORICAL_FAILED_SONNET_OUTPUT_BUDGET_CHARACTERIZATION_ATTEMPT = MappingProxyType({
    "root": r"C:\TORMENT\m5s5c",
    "run_id": "meridian-n5-sonnet5c-20260824-a-private",
    "condition": "A_PRIVATE",
    "logical_call": "round_1:researcher_001",
    "model_id": FROZEN_MODEL_ID,
    "max_tokens": 1024,
    "attempted_provider_calls": 1,
    "succeeded_provider_calls": 0,
    "failed_provider_calls": 1,
    "retry_count": 0,
    "status": "FAILED",
    "scientific_interpretation": "OUTPUT-BUDGET EXHAUSTION",
    "cause": "ThinkingBlock only; no TextBlock; stop_reason=max_tokens",
})
HISTORICAL_FAILED_SONNET_TIMEOUT_CHARACTERIZATION_ATTEMPT = MappingProxyType({
    "root": r"C:\TORMENT\m5s5d",
    "run_id": "meridian-n5-sonnet5d-20260824-a-private",
    "condition": "A_PRIVATE",
    "logical_call": "round_1:researcher_001",
    "model_id": FROZEN_MODEL_ID,
    "max_tokens": FROZEN_MAX_TOKENS,
    "timeout_seconds": 30,
    "attempted_provider_calls": 1,
    "succeeded_provider_calls": 0,
    "failed_provider_calls": 1,
    "retry_count": 0,
    "status": "FAILED",
    "scientific_interpretation": "TIMEOUT",
    "cause": "Request timed out or interrupted",
})
HISTORICAL_FAILED_SONNET_SCHEMA_CHARACTERIZATION_ATTEMPT = MappingProxyType({
    "root": r"C:\TORMENT\m5s5e",
    "run_id": "meridian-n5-sonnet5e-20260824-a-private",
    "condition": "A_PRIVATE",
    "logical_call": "round_2:researcher_005",
    "model_id": FROZEN_MODEL_ID,
    "max_tokens": FROZEN_MAX_TOKENS,
    "timeout_seconds": FROZEN_TIMEOUT_SECONDS,
    "attempted_provider_calls": 10,
    "succeeded_provider_calls": 9,
    "failed_provider_calls": 1,
    "retry_count": 0,
    "status": "FAILED",
    "scientific_interpretation": "MODEL OUTPUT CONTRACT NONCOMPLIANCE — MINOR EXTRA-FIELD DEVIATION",
    "cause": "finding index 1 had forbidden extra stance_note field",
})
SONNET5F_EXACT_SCHEMA_SUCCESSOR_CHARACTERIZATION_ROOT = r"C:\TORMENT\m5s5f"
SONNET5F_EXACT_SCHEMA_SUCCESSOR_RUN_IDS = MappingProxyType({
    "A_PRIVATE": "meridian-n5-sonnet5f-20260824-a-private",
    "B1_TORMENT_MECHANISMS_ONLY": "meridian-n5-sonnet5f-20260824-b1-mechanisms-only",
    "B2_TORMENT_SALIENCE_SURFACED": "meridian-n5-sonnet5f-20260824-b2-salience-surfaced",
    "C_NAIVE_SHARED_CONTENT": "meridian-n5-sonnet5f-20260824-c-naive-shared-content",
})
_CARD_ID = re.compile(r"^[RMDCPN]-\d{3}$")
_VALID_STANCES = frozenset({"asserts", "refutes", "mentions"})
_SAMPLING_DEFAULT = {"mode": "provider_default", "explicit_value": None}
_OUTPUT_KEYS = frozenset({"findings", "claims", "final_answer", "collective_context_consumed"})
_FINDING_KEYS = frozenset({"text", "card_ids", "share_permitted"})
_CLAIM_KEYS = frozenset({"text", "card_ids", "stance"})
_FINAL_ANSWER_KEYS = frozenset({"root_cause", "contributing_factors", "cited_card_ids"})


class MeridianProviderResponseError(ValueError):
    """The model response does not meet the frozen Meridian output contract."""


@dataclass(frozen=True)
class MeridianDotenvBootstrap:
    """Redacted result of the experiment-local, non-overriding dotenv bootstrap."""

    dotenv_path: str
    dotenv_loaded: bool
    credential_configured: bool
    credential_source: str


def load_repo_dotenv_safely(
    *,
    environment: MutableMapping[str, str] | None = None,
    dotenv_path: Path = REPO_DOTENV_PATH,
) -> MeridianDotenvBootstrap:
    """Load the repository `.env` without overriding process environment values.

    This follows the user-facing tool convention. The returned status never
    includes credential values; callers must use it only to report readiness.
    """

    env = environment if environment is not None else os.environ
    api_key_env = AnthropicNonSpineLLMProviderAdapter.API_KEY_ENV
    credential_existed_before_bootstrap = api_key_env in env
    try:
        resolved = Path(dotenv_path).resolve()
    except OSError:
        resolved = Path(dotenv_path)
    loaded = False
    if resolved.exists() and resolved.is_file():
        try:
            with open(resolved, "r", encoding="utf-8") as fh:
                for raw_line in fh:
                    line = raw_line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip()
                    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
                        value = value[1:-1]
                    if key and key not in env:
                        env[key] = value
            loaded = True
        except OSError:
            pass
    credential_source = (
        "process_environment" if credential_existed_before_bootstrap
        else "repo_dotenv" if api_key_env in env
        else "absent"
    )
    return MeridianDotenvBootstrap(
        dotenv_path=str(resolved),
        dotenv_loaded=loaded,
        credential_configured=credential_source != "absent",
        credential_source=credential_source,
    )


class _FrozenAnthropicEnvironment:
    """Delegates normal reads but pins the non-secret model and timeout configuration."""

    def __init__(self, base: Mapping[str, str], model_id: str, timeout_seconds: int) -> None:
        self._base = base
        self._model_id = model_id
        self._timeout_seconds = timeout_seconds

    def get(self, key: str, default: Any = None) -> Any:
        if key == AnthropicNonSpineLLMProviderAdapter.MODEL_ENV:
            return self._model_id
        if key == AnthropicNonSpineLLMProviderAdapter.TIMEOUT_ENV:
            return str(self._timeout_seconds)
        return self._base.get(key, default)


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _card_ids(value: object, *, field: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(card_id, str) for card_id in value):
        raise MeridianProviderResponseError(f"{field} must be a list of card IDs")
    if any(not _CARD_ID.fullmatch(card_id) or card_id not in CARD_IDS for card_id in value):
        raise MeridianProviderResponseError(f"{field} contains an invalid card ID")
    return list(value)


def _nonempty_text(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise MeridianProviderResponseError(f"{field} must be a non-empty string")
    return value


def parse_meridian_response(raw_text: str) -> dict[str, Any]:
    """Parse exactly one strict JSON object; no prose extraction or coercion."""
    if not isinstance(raw_text, str):
        raise MeridianProviderResponseError("provider response must be text")
    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise MeridianProviderResponseError("provider response is not valid JSON") from exc
    if not isinstance(payload, dict) or set(payload) != _OUTPUT_KEYS:
        raise MeridianProviderResponseError("provider response has an unexpected top-level structure")
    if not isinstance(payload["findings"], list):
        raise MeridianProviderResponseError("findings must be a list")
    if not isinstance(payload["claims"], list):
        raise MeridianProviderResponseError("claims must be a list")
    findings: list[dict[str, Any]] = []
    for finding in payload["findings"]:
        if not isinstance(finding, dict) or set(finding) != _FINDING_KEYS:
            raise MeridianProviderResponseError("finding has an unexpected structure")
        if not isinstance(finding["share_permitted"], bool):
            raise MeridianProviderResponseError("finding share_permitted must be boolean")
        findings.append({
            "text": _nonempty_text(finding["text"], field="finding text"),
            "card_ids": _card_ids(finding["card_ids"], field="finding card_ids"),
            "share_permitted": finding["share_permitted"],
        })
    claims: list[dict[str, Any]] = []
    for claim in payload["claims"]:
        if not isinstance(claim, dict) or set(claim) != _CLAIM_KEYS:
            raise MeridianProviderResponseError("claim has an unexpected structure")
        if claim["stance"] not in _VALID_STANCES:
            raise MeridianProviderResponseError("claim has an invalid stance")
        claims.append({
            "text": _nonempty_text(claim["text"], field="claim text"),
            "card_ids": _card_ids(claim["card_ids"], field="claim card_ids"),
            "stance": claim["stance"],
        })
    final_answer = payload["final_answer"]
    if not isinstance(final_answer, dict) or set(final_answer) != _FINAL_ANSWER_KEYS:
        raise MeridianProviderResponseError("final_answer has an unexpected structure")
    factors = final_answer["contributing_factors"]
    if not isinstance(factors, list) or not all(isinstance(factor, str) for factor in factors):
        raise MeridianProviderResponseError("final_answer contributing_factors must be a list of strings")
    if not isinstance(payload["collective_context_consumed"], bool):
        raise MeridianProviderResponseError("collective_context_consumed must be boolean")
    return {
        "findings": findings,
        "claims": claims,
        "final_answer": {
            "root_cause": _nonempty_text(final_answer["root_cause"], field="final_answer root_cause"),
            "contributing_factors": list(factors),
            "cited_card_ids": _card_ids(final_answer["cited_card_ids"], field="final_answer cited_card_ids"),
        },
        "collective_context_consumed": payload["collective_context_consumed"],
    }


class FrozenAnthropicMeridianProvider:
    """Experiment-local, stateless bridge from Meridian to the native Anthropic adapter."""

    def __init__(
        self,
        *,
        native_adapter: NonSpineLLMProviderAdapter | None = None,
        model_id: str = FROZEN_MODEL_ID,
        environment: Mapping[str, str] | None = None,
    ) -> None:
        if model_id != FROZEN_MODEL_ID:
            raise ValueError("Meridian v1 requires the frozen Anthropic model ID")
        if AnthropicNonSpineLLMProviderAdapter.DEFAULT_TIMEOUT_SECONDS != 30:
            raise ValueError("native Anthropic adapter no longer has Meridian's frozen timeout")
        self._model_id = model_id
        self._environment = environment if environment is not None else os.environ
        self._native_adapter = native_adapter or AnthropicNonSpineLLMProviderAdapter(
            env=_FrozenAnthropicEnvironment(
                self._environment, self._model_id, FROZEN_TIMEOUT_SECONDS,
            ),
            max_tokens=FROZEN_MAX_TOKENS,
            timeout_seconds=FROZEN_TIMEOUT_SECONDS,
        )

    @classmethod
    def from_repo_dotenv(
        cls,
        *,
        native_adapter: NonSpineLLMProviderAdapter | None = None,
        environment: MutableMapping[str, str] | None = None,
        dotenv_path: Path = REPO_DOTENV_PATH,
    ) -> tuple["FrozenAnthropicMeridianProvider", MeridianDotenvBootstrap]:
        """Bootstrap the local environment before constructing the frozen bridge."""

        env = environment if environment is not None else os.environ
        bootstrap = load_repo_dotenv_safely(environment=env, dotenv_path=dotenv_path)
        return cls(native_adapter=native_adapter, environment=env), bootstrap

    def metadata(self) -> dict[str, Any]:
        return {
            "provider": "AnthropicNonSpineLLMProviderAdapter",
            "model_id": self._model_id,
            "provider_mode": "live",
            "session_isolation": "per_agent_per_round",
            "retry_policy": "none",
            "sampling": {
                "max_tokens": {"mode": "explicit", "explicit_value": FROZEN_MAX_TOKENS},
                "temperature": copy.deepcopy(_SAMPLING_DEFAULT),
                "top_p": copy.deepcopy(_SAMPLING_DEFAULT),
                "top_k": copy.deepcopy(_SAMPLING_DEFAULT),
                "thinking": copy.deepcopy(_SAMPLING_DEFAULT),
                "timeout": {"mode": "explicit", "explicit_value": FROZEN_TIMEOUT_SECONDS},
                "system_instruction": {
                    "mode": "harness_instruction",
                    "sha256": payload_sha256(RESEARCH_INSTRUCTION),
                },
            },
        }

    @staticmethod
    def render_prompt(
        *,
        agent_id: str,
        round_number: int,
        instruction: str,
        assigned_cards: Sequence[Mapping[str, str]],
        collective_context: Mapping[str, Any] | None,
        naive_shared_findings: Sequence[Mapping[str, Any]],
    ) -> str:
        if instruction != RESEARCH_INSTRUCTION:
            raise ValueError("Meridian bridge requires the frozen research instruction")
        if round_number not in {1, 2}:
            raise ValueError("Meridian bridge accepts rounds 1 and 2 only")
        if collective_context is not None and naive_shared_findings:
            raise ValueError("Meridian bridge forbids mixed collective and naive sharing")
        cards = sorted((dict(card) for card in assigned_cards), key=lambda card: card["card_id"])
        payload: dict[str, Any] = {
            "agent_id": agent_id,
            "assigned_cards": cards,
            "response_schema": {
                "findings": [{"text": "string", "card_ids": ["CARD-ID"], "share_permitted": "boolean"}],
                "claims": [{"text": "string", "card_ids": ["CARD-ID"], "stance": "asserts|refutes|mentions"}],
                "final_answer": {
                    "root_cause": "string",
                    "contributing_factors": ["string"],
                    "cited_card_ids": ["CARD-ID"],
                },
                "collective_context_consumed": "boolean",
            },
            "round_number": round_number,
        }
        if collective_context is not None:
            payload["collective_context"] = copy.deepcopy(dict(collective_context))
        if naive_shared_findings:
            payload["naive_shared_findings"] = sorted(
                (copy.deepcopy(dict(finding)) for finding in naive_shared_findings),
                key=_canonical_json,
            )
        return (
            "Return exactly one JSON object matching response_schema. "
            "Every object must contain exactly the keys shown in response_schema. "
            "Do not add any additional keys, annotations, metadata, notes, explanations, or fields. "
            "Do not use markdown fences or add prose before or after the object.\n"
            + _canonical_json(payload)
        )

    def run_round(
        self,
        *,
        agent_id: str,
        round_number: int,
        instruction: str,
        assigned_cards: Sequence[Mapping[str, str]],
        collective_context: Mapping[str, Any] | None,
        naive_shared_findings: Sequence[Mapping[str, Any]],
    ) -> ProviderRoundResponse:
        prompt = self.render_prompt(
            agent_id=agent_id,
            round_number=round_number,
            instruction=instruction,
            assigned_cards=assigned_cards,
            collective_context=collective_context,
            naive_shared_findings=naive_shared_findings,
        )
        result = self._native_adapter.generate(NonSpineLLMProviderRequest(
            prompt_request=NonSpineLLMPromptRequest(
                system_text=instruction,
                rendered_prompt=prompt,
            ),
            config=NonSpineLLMProviderConfig(
                provider_name="anthropic",
                model_name=self._model_id,
                is_fake=False,
                network_enabled=True,
            ),
        ))
        if result.is_fake or not result.provider_called or result.model_name != self._model_id:
            raise MeridianProviderResponseError("native provider did not produce the frozen live-model result")
        raw_text = result.text
        request_metadata = {
            "provider_visible_prompt_sha256": payload_sha256({
                "system_instruction": instruction,
                "rendered_prompt": prompt,
            }),
        }
        response_metadata = {
            "provider_called": result.provider_called,
            "provider_name": result.provider_name,
            "model_name": result.model_name,
        }
        try:
            parsed = parse_meridian_response(raw_text)
        except MeridianProviderResponseError as exc:
            return ProviderRoundResponse(
                output={},
                raw_response_text=raw_text,
                usage=None,
                response_metadata=response_metadata,
                request_metadata=request_metadata,
                parser_error=str(exc),
            )
        return ProviderRoundResponse(
            output=parsed,
            raw_response_text=raw_text,
            usage=None,
            response_metadata=response_metadata,
            request_metadata=request_metadata,
        )

    def preflight(self) -> dict[str, Any]:
        """Report presence/configuration only; never read a credential or contact Anthropic."""
        return {
            "anthropic_sdk_available": importlib.util.find_spec("anthropic") is not None,
            "credential_configured": AnthropicNonSpineLLMProviderAdapter.API_KEY_ENV in self._environment,
            "real_provider_gate_configured": AnthropicNonSpineLLMProviderAdapter.GATE_ENV in self._environment,
            "model_id": self._model_id,
            "adapter_construction_possible": isinstance(self._native_adapter, NonSpineLLMProviderAdapter),
            "network_contact_performed": False,
        }
