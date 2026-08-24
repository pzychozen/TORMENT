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
from collections.abc import Mapping, Sequence
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


FROZEN_MODEL_ID = "claude-haiku-4-5-20251001"
_CARD_ID = re.compile(r"^[RMDCPN]-\d{3}$")
_VALID_STANCES = frozenset({"asserts", "refutes", "mentions"})
_SAMPLING_DEFAULT = {"mode": "provider_default", "explicit_value": None}
_OUTPUT_KEYS = frozenset({"findings", "claims", "final_answer", "collective_context_consumed"})
_FINDING_KEYS = frozenset({"text", "card_ids", "share_permitted"})
_CLAIM_KEYS = frozenset({"text", "card_ids", "stance"})
_FINAL_ANSWER_KEYS = frozenset({"root_cause", "contributing_factors", "cited_card_ids"})


class MeridianProviderResponseError(ValueError):
    """The model response does not meet the frozen Meridian output contract."""


class _FrozenAnthropicEnvironment:
    """Delegates normal reads but pins the non-secret model and timeout configuration."""

    def __init__(self, base: Mapping[str, str], model_id: str) -> None:
        self._base = base
        self._model_id = model_id

    def get(self, key: str, default: Any = None) -> Any:
        if key == AnthropicNonSpineLLMProviderAdapter.MODEL_ENV:
            return self._model_id
        if key == AnthropicNonSpineLLMProviderAdapter.TIMEOUT_ENV:
            return "30"
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
            raise ValueError("Meridian v1 requires the frozen dated Anthropic model ID")
        if AnthropicNonSpineLLMProviderAdapter.MAX_TOKENS != 1024:
            raise ValueError("native Anthropic adapter no longer has Meridian's frozen max_tokens")
        if AnthropicNonSpineLLMProviderAdapter.DEFAULT_TIMEOUT_SECONDS != 30:
            raise ValueError("native Anthropic adapter no longer has Meridian's frozen timeout")
        self._model_id = model_id
        self._environment = environment if environment is not None else os.environ
        self._native_adapter = native_adapter or AnthropicNonSpineLLMProviderAdapter(
            env=_FrozenAnthropicEnvironment(self._environment, self._model_id),
        )

    def metadata(self) -> dict[str, Any]:
        return {
            "provider": "AnthropicNonSpineLLMProviderAdapter",
            "model_id": self._model_id,
            "provider_mode": "live",
            "session_isolation": "per_agent_per_round",
            "retry_policy": "none",
            "sampling": {
                "max_tokens": {"mode": "explicit", "explicit_value": 1024},
                "temperature": copy.deepcopy(_SAMPLING_DEFAULT),
                "top_p": copy.deepcopy(_SAMPLING_DEFAULT),
                "top_k": copy.deepcopy(_SAMPLING_DEFAULT),
                "thinking": copy.deepcopy(_SAMPLING_DEFAULT),
                "timeout": {"mode": "explicit", "explicit_value": 30},
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
            "Return exactly one JSON object matching response_schema. Do not use markdown fences "
            "or add prose before or after the object.\n"
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
