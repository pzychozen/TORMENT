from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
import tempfile
import types
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "examples" / "lived_use_chat.py"
SPEC = importlib.util.spec_from_file_location("lived_use_chat_under_test", MODULE_PATH)
luc = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = luc
assert SPEC.loader is not None
SPEC.loader.exec_module(luc)


REFERENCE_CLIENT_LF_HASHES = {
    "examples/ryuki_chat.py": "4FF54209820855CB3E453BB670B0AA5C25752F5738E0AF0B2EF7A48CE5002F7A",
    "examples/ryuki_chat_openai.py": "57CCE167D9028F8537506C7330E587EFF5A1CDFF72A8BDAA004C9C98526BE7F7",
    "examples/ryuki_chat_v2_matrix.py": "31C78230DF9DFD603F047FDDE62E610A0C9CE33117CA184101DB2E4395BB552D",
    "live_agent/demo/chat_ryuki_nox.py": "47802F7C0655DA98427840E213A02E161FC1DAE583F13C5DC75FE40FDC86FAF8",
    "examples/character_chat_probe.py": "3FB43257EBC6F0524A48D59A51BA7FDEEA5C0F96A9B91AE69C7A61D7C154B4DF",
}


def _character():
    return luc.load_character_spec(ROOT / "examples" / "lived_use_character_v1.yaml")


def _health(**overrides):
    data = {
        "ok": True,
        "version": "2.4.7",
        "profile": {
            "name": "companion",
            "known": True,
            "applied_count": 3,
            "applied_keys": ["TORMENT_AFFECT_ENABLE", "TORMENT_ROLE_ENABLE"],
        },
        "embedder": {
            "provider": "st",
            "model": "BAAI/bge-small-en-v1.5",
            "dim": 384,
            "cache_size": 0,
        },
        "embedder_degraded": False,
        "embedder_error": "",
        "requested_embedder": {
            "provider": "st",
            "model": "BAAI/bge-small-en-v1.5",
            "strict": True,
        },
    }
    for key, value in overrides.items():
        data[key] = value
    return data


def _config():
    effective = {}
    for key in luc.CONFIG_EFFECTIVE_KEYS:
        effective[key] = {"value": "1", "default": "0", "source": "env_override"}
    effective["TORMENT_DATA_DIR"] = {
        "value": r"C:\TORMENT\TORMENT_repo\TORMENT-fabric_v2\torment_fabric\data\lived_use\eira_voss\a0",
        "default": "<auto>",
        "source": "env_override",
    }
    effective["TORMENT_PROFILE"] = {"value": "companion", "default": "", "source": "env_override"}
    effective["TORMENT_EMBED_PROVIDER"] = {"value": "st", "default": "hash", "source": "env_override"}
    effective["TORMENT_EMBED_MODEL"] = {
        "value": "BAAI/bge-small-en-v1.5",
        "default": "",
        "source": "env_override",
    }
    effective["TORMENT_EMBED_DEVICE"] = {"value": "cpu", "default": "cpu", "source": "env_override"}
    effective["TORMENT_EMBED_STRICT"] = {"value": "1", "default": "0", "source": "env_override"}
    effective["UNRELATED"] = {"value": "do-not-capture", "default": "", "source": "default"}
    return {
        "ok": True,
        "effective": effective,
        "derived": {
            "profile": {"name": "companion", "known": True, "applied_count": 3},
            "embed": {"strict": True, "cache_enabled": False},
        },
    }


def _metrics():
    return {
        "workspace_id": "default",
        "agent_id": None,
        "features": {
            "compress_enable": False,
            "hivemind_enable": False,
            "srg_enable": False,
            "character_enable": True,
            "checkpoint_enable": True,
        },
        "agents": {
            luc.EXPECTED_AGENT_ID: {
                "memory_count": 3,
                "compression": {
                    "last_compression_step": 0,
                    "compression_events_total": 0,
                    "warning_active": False,
                    "prev_in_corridor": True,
                },
                "compression_recent": [{"raw": "not retained"}],
                "deep_memory": {"raw": "not retained"},
                "character": {
                    "drift_score": 0.02,
                    "drift_direction": "stable",
                    "distance_to_seed": 0.1,
                    "core_count": 1,
                    "relational_count": 2,
                    "situational_count": 0,
                },
            }
        },
        "domains": {
            "personal": {
                "motif_count": 2,
                "motif_avg_strength": 0.4,
                "motif_max_strength": 0.8,
                "shared_memory_count": 0,
                "proposals_total": 0,
                "coherence_field": {"basin_count": 1, "ridge_count": 0, "plateau_count": 1},
            }
        },
        "collective": {"packet_count": 0, "convergence_events": 0},
        "counts": {"invented": True},
        "memory": {"invented": True},
        "requests": {"invented": True},
    }


def _profiles():
    return {
        "ok": True,
        "active": {
            "name": "companion",
            "known": True,
            "applied_count": 2,
            "applied": {
                "TORMENT_AFFECT_ENABLE": "1",
                "TORMENT_ROLE_ENABLE": "1",
                "NON_TORMENT": "not-retained",
            },
        },
        "profiles": {"companion": {"raw": "not retained"}},
    }


def _identity(**seed_overrides):
    char = _character()
    seed = copy.deepcopy(char.seed)
    seed.update(seed_overrides)
    return {
        "workspace_id": char.workspace_id,
        "agent_id": char.agent_id,
        "seed": seed,
        "overlay": {"raw": "not retained"},
        "updated_ts": 123,
    }


def _recent(step=None, ok=True, malformed=False):
    if malformed:
        return {"ok": True, "results": [{"eid": 1, "summary": "missing step"}], "count": 1}
    if step is None:
        return {"ok": ok, "results": [], "count": 0}
    return {
        "ok": ok,
        "results": [
            {
                "eid": 44,
                "kind": "memory",
                "tier": "core",
                "provenance_type": "source_memory",
                "memory_class": "core",
                "step": int(step),
                "created_at": "2026-08-03T00:00:00Z",
                "summary": "not captured for step resume",
            }
        ],
        "count": 1,
    }


def _explain():
    return {
        "sim": 0.71,
        "strength": 0.8,
        "recency_days": 0.25,
        "motif_alignment": 0.33,
        "contradiction_risk": 0.0,
        "weights": {"alpha": 0.35, "beta": 0.10, "gamma": 0.20, "delta": 0.30},
        "collective_discount": 1.0,
        "tool_result_discount": 1.0,
        "conflict_penalty": 1.0,
        "conflict_status": None,
        "conflict_ids": [12, "c-2"],
        "provenance_type": "source_memory",
        "self_thread_bonus": 0.01,
        "self_anchor_bonus": 0.02,
        "thread_window_bonus": 0.03,
        "affect_match_bonus": 0.04,
        "mood_drift_bonus": 0.05,
        "mood_spiral_penalty": 0.0,
        "continuity_total_adjustment": 0.15,
        "srg_same_band_bonus": 1.0,
        "srg_crystal_bonus": 1.0,
        "srg_heartbeat_bonus": 1.0,
        "srg_total_multiplier": 1.0,
        "srg_active_modifiers": ["same_band"],
        "memory_plan_lane": "core",
        "lane_weight": 1.0,
        "lane_weight_applied": True,
    }


def _continuity_debug():
    return {
        "mode": "character_continuity",
        "bonuses_enabled": {
            "self_thread": True,
            "thread_window": True,
            "identity_anchors": True,
            "affect_match": True,
            "mood_drift": True,
            "mood_spiral": True,
        },
        "query_signals": {
            "personal_query": True,
            "query_affect_tag": "curious",
            "query_affect_conf": 0.7,
            "dominant_role": "explorer",
        },
        "applied_bonuses_summary": {
            "self_thread": 1,
            "self_anchor": 1,
            "thread_window": 1,
            "affect_match": 1,
            "mood_drift": 1,
            "mood_spiral_penalty": 0,
        },
        "top_hits_bonus_breakdown": [
            {
                "eid": 7,
                "base_score": 0.7,
                "final_score": 0.85,
                "bonuses": {
                    "self_thread": 0.01,
                    "self_anchor": 0.02,
                    "thread_window": 0.03,
                    "affect_match": 0.04,
                    "mood_drift": 0.05,
                    "unretained": 9,
                },
            }
        ],
    }


def _query_response(seed_preamble="TORMENT-returned seed preamble."):
    return {
        "domains": [{"id": "personal", "score": 1.0}],
        "domain_used": ["personal"],
        "bridge_peek_domains": [],
        "results": [
            {
                "eid": 7,
                "summary": "Hilmir asked whether strange ideas can be explored seriously.",
                "score": 0.77,
                "final_score": 0.8732,
                "character_tier": "core",
                "provenance_type": "source_memory",
                "scope": "private",
                "domain_id": "personal",
                "authority_status": "ok",
                "explain": _explain(),
            }
        ],
        "filter_excluded": [{"eid": 99, "scope": "private", "domain_id": "personal", "reason": "non_shareable"}],
        "_core_hits_in_count": 2,
        "_authority_guard_rejected": 0,
        "continuity_debug": _continuity_debug(),
        "character_context": {
            "seed_id": luc.EXPECTED_SEED_ID,
            "character_name": luc.EXPECTED_CHARACTER_NAME,
            "seed_preamble": seed_preamble,
            "recommendations": ["Stay concise.", "Prefer honesty over performance."],
            "drift_score": 0.12,
            "drift_direction": "stable",
            "drift_summary": "steady",
            "character_tier": "core",
            "seed_basin_role": "basin",
            "relational_count": 3,
            "tier_breakdown": {"core": 1, "relational": 3, "situational": 0},
            "spirit_return_summary": "none",
            "unretained": {"raw": "no"},
        },
    }


def _ingest_response(**overrides):
    data = {
        "ok": True,
        "stored": True,
        "reinforced": False,
        "eid": 101,
        "path": "fast",
        "escalated": False,
        "result_code": "stored",
        "decision_code": "fast_allowed",
    }
    data.update(overrides)
    return data


class FakeTorment:
    def __init__(
        self,
        *,
        health=None,
        config=None,
        metrics=None,
        profiles=None,
        identity=None,
        recent=None,
        query_response=None,
        workspace_error=None,
        agent_error=None,
        query_error=None,
        ingest_error=None,
        ingest_response=None,
    ):
        self.health_response = health if health is not None else _health()
        self.config_response = config if config is not None else _config()
        self.metrics_response = metrics if metrics is not None else _metrics()
        self.profiles_response = profiles if profiles is not None else _profiles()
        self.identity_response = identity if identity is not None else _identity()
        self.recent_response = recent if recent is not None else _recent()
        self.query_response = query_response if query_response is not None else _query_response()
        self.workspace_error = workspace_error
        self.agent_error = agent_error
        self.query_error = query_error
        self.ingest_error = ingest_error
        self.ingest_response = ingest_response
        self.calls = []
        self.query_payloads = []
        self.ingest_payloads = []

    def health(self):
        self.calls.append(("health", None))
        return copy.deepcopy(self.health_response)

    def config(self):
        self.calls.append(("config", None))
        return copy.deepcopy(self.config_response)

    def debug_metrics(self):
        self.calls.append(("debug_metrics", None))
        return copy.deepcopy(self.metrics_response)

    def profiles(self):
        self.calls.append(("profiles", None))
        return copy.deepcopy(self.profiles_response)

    def workspace_create(self, workspace_id, domains):
        payload = {"workspace_id": workspace_id, "domains": list(domains)}
        self.calls.append(("workspace_create", payload))
        if self.workspace_error is not None:
            raise self.workspace_error
        return payload

    def agent_create(self, workspace_id, agent_id, seed):
        payload = {"workspace_id": workspace_id, "agent_id": agent_id, "seed": copy.deepcopy(seed)}
        self.calls.append(("agent_create", payload))
        if self.agent_error is not None:
            raise self.agent_error
        return payload

    def agent_identity(self, workspace_id, agent_id):
        payload = copy.deepcopy(self.identity_response)
        self.calls.append(("agent_identity", {"workspace_id": workspace_id, "agent_id": agent_id}))
        return payload

    def recent_index(self, workspace_id, agent_id, limit=1):
        self.calls.append(("recent_index", {"workspace_id": workspace_id, "agent_id": agent_id, "limit": limit}))
        return copy.deepcopy(self.recent_response)

    def thinking_debug(self, payload):
        self.calls.append(("thinking_debug", copy.deepcopy(payload)))
        return {"ok": True, "result": {"raw": "not retained"}}

    def query(self, payload):
        self.calls.append(("query", copy.deepcopy(payload)))
        self.query_payloads.append(copy.deepcopy(payload))
        if self.query_error is not None:
            raise self.query_error
        return copy.deepcopy(self.query_response)

    def ingest(self, payload):
        self.calls.append(("ingest", copy.deepcopy(payload)))
        self.ingest_payloads.append(copy.deepcopy(payload))
        if self.ingest_error is not None:
            if isinstance(self.ingest_error, list):
                if self.ingest_error:
                    error = self.ingest_error.pop(0)
                    if error is not None:
                        raise error
            else:
                raise self.ingest_error
        if self.ingest_response is not None:
            response = copy.deepcopy(self.ingest_response)
            if "step" not in response:
                response["step"] = payload["step"]
            return response
        return {"ok": True, "stored": True, "eid": 101, "step": payload["step"]}


class FakeProvider:
    def __init__(
        self,
        *,
        name="anthropic",
        model="test-model",
        reply="A steady answer.",
        error=None,
        result=None,
    ):
        self.name = name
        self.model = model
        self.reply = reply
        self.error = error
        self.result = result
        self.calls = []

    def generate(self, *, system_prompt, messages, max_tokens):
        self.calls.append(
            {
                "system_prompt": system_prompt,
                "messages": copy.deepcopy(messages),
                "max_tokens": max_tokens,
            }
        )
        if self.error is not None:
            raise self.error
        if self.result is not None:
            return self.result
        return luc.ProviderResult(
            text=self.reply,
            stop_reason="end_turn",
            content_block_types=["text"],
            input_tokens=11,
            output_tokens=7,
            thinking_tokens=None,
        )


class FakeMessages:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(copy.deepcopy(kwargs))
        return self.response


class FakeAnthropicSdk:
    def __init__(self, response):
        self.messages = FakeMessages(response)


class FakeHttpResponse:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code

    def json(self):
        return copy.deepcopy(self.payload)


class FakeHttpPost:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def __call__(self, url, *, headers, json, timeout):
        self.calls.append(
            {
                "url": url,
                "headers": copy.deepcopy(headers),
                "json": copy.deepcopy(json),
                "timeout": timeout,
            }
        )
        return FakeHttpResponse(self.payload)


def _anthropic_response(content, stop_reason="end_turn", input_tokens=5, output_tokens=3, thinking_tokens=None):
    usage = types.SimpleNamespace(input_tokens=input_tokens, output_tokens=output_tokens)
    if thinking_tokens is not None:
        usage.thinking_tokens = thinking_tokens
    return types.SimpleNamespace(content=content, stop_reason=stop_reason, usage=usage)


def _anthropic_http_payload(content, stop_reason="end_turn", input_tokens=5, output_tokens=3, thinking_tokens=None):
    usage = {"input_tokens": input_tokens, "output_tokens": output_tokens}
    if thinking_tokens is not None:
        usage["thinking_tokens"] = thinking_tokens
    return {"content": content, "stop_reason": stop_reason, "usage": usage}


def _chat_payload(content="answer", finish_reason="stop", usage=None, tool_calls=None, include_content=True):
    message = {}
    if include_content:
        message["content"] = content
    if tool_calls is not None:
        message["tool_calls"] = tool_calls
    return {
        "choices": [{"finish_reason": finish_reason, "message": message}],
        "usage": usage if usage is not None else {"prompt_tokens": 4, "completion_tokens": 2},
    }


class MemoryRecorder:
    active = True

    def __init__(self):
        self.events = []
        self.closed = False

    def record(self, event_type, payload):
        event = {"event_type": event_type}
        event.update(copy.deepcopy(payload))
        self.events.append(event)

    def close(self):
        self.closed = True


class FailingRecorder:
    active = True

    def __init__(self):
        self.record_calls = 0
        self.disabled = False
        self.warned = False

    def record(self, event_type, payload):
        self.record_calls += 1
        raise OSError("write failed")

    def disable(self):
        self.disabled = True

    def warn_once(self):
        self.warned = True


def _session(torment=None, provider=None, recorder=None, environ=None, run_id="run-a0"):
    return luc.LivedUseSession(
        torment=torment or FakeTorment(),
        provider=provider or FakeProvider(),
        character=_character(),
        recorder=recorder or luc.JsonlRecorder(path=None, enabled=False),
        run_id=run_id,
        top_k=8,
        environ=environ or {},
    )


def _preflighted(torment=None, provider=None, recorder=None, environ=None):
    torment = torment or FakeTorment()
    provider = provider or FakeProvider()
    session = _session(torment=torment, provider=provider, recorder=recorder, environ=environ)
    session.preflight()
    return session, torment, provider


def _call_names(torment):
    return [name for name, _payload in torment.calls]


def _events_of(recorder, event_type):
    return [event for event in recorder.events if event["event_type"] == event_type]


def test_anthropic_sdk_single_text_block_succeeds():
    sdk = FakeAnthropicSdk(_anthropic_response([types.SimpleNamespace(type="text", text="hello")]))
    provider = luc.AnthropicProvider("secret", "claude-test", sdk_client=sdk)

    result = provider.generate(system_prompt="sys", messages=[{"role": "user", "content": "hi"}], max_tokens=40)

    assert result.text == "hello"
    assert result.stop_reason == "end_turn"
    assert result.content_block_types == ["text"]
    assert result.input_tokens == 5
    assert result.output_tokens == 3


def test_anthropic_thinking_block_followed_by_text_returns_only_text():
    sdk = FakeAnthropicSdk(
        _anthropic_response(
            [
                types.SimpleNamespace(type="thinking", thinking="hidden chain"),
                types.SimpleNamespace(type="text", text="visible"),
            ],
            thinking_tokens=17,
        )
    )
    provider = luc.AnthropicProvider("secret", "claude-test", sdk_client=sdk)

    result = provider.generate(system_prompt="sys", messages=[], max_tokens=40)

    assert result.text == "visible"
    assert result.content_block_types == ["thinking", "text"]
    assert result.thinking_tokens == 17
    assert "hidden chain" not in result.text


def test_anthropic_multiple_text_blocks_concatenate_exactly_in_order():
    sdk = FakeAnthropicSdk(
        _anthropic_response(
            [
                types.SimpleNamespace(type="text", text="first"),
                types.SimpleNamespace(type="text", text="\nsecond"),
                types.SimpleNamespace(type="text", text=" third"),
            ]
        )
    )
    provider = luc.AnthropicProvider("secret", "claude-test", sdk_client=sdk)

    result = provider.generate(system_prompt="sys", messages=[], max_tokens=40)

    assert result.text == "first\nsecond third"


@pytest.mark.parametrize(
    "content,stop_reason",
    [
        ([types.SimpleNamespace(type="thinking", thinking="hidden only")], "end_turn"),
        ([types.SimpleNamespace(type="text", text="")], "end_turn"),
        ([types.SimpleNamespace(type="text", text="   \n\t")], "end_turn"),
        ([types.SimpleNamespace(type="text", text="partial")], "max_tokens"),
        ([types.SimpleNamespace(type="text", text="no")], "refusal"),
        ([types.SimpleNamespace(type="text", text="tool")], "tool_use"),
        ([types.SimpleNamespace(type="text", text="pause")], "pause_turn"),
        ([types.SimpleNamespace(type="text", text="missing")], None),
        ([types.SimpleNamespace(type="text", text="mystery")], "unexpected_reason"),
    ],
)
def test_anthropic_sdk_incomplete_responses_fail_closed(content, stop_reason):
    sdk = FakeAnthropicSdk(_anthropic_response(content, stop_reason=stop_reason))
    provider = luc.AnthropicProvider("secret", "claude-test", sdk_client=sdk)

    with pytest.raises(luc.ProviderResponseError) as exc:
        provider.generate(system_prompt="sys", messages=[], max_tokens=40)

    assert exc.value.result.stop_reason == stop_reason


def test_anthropic_raw_http_parsing_matches_sdk_parsing():
    sdk_blocks = [
        types.SimpleNamespace(type="thinking", thinking="hidden"),
        types.SimpleNamespace(type="text", text="one"),
        types.SimpleNamespace(type="text", text="two"),
    ]
    http_blocks = [
        {"type": "thinking", "thinking": "hidden"},
        {"type": "text", "text": "one"},
        {"type": "text", "text": "two"},
    ]
    sdk_provider = luc.AnthropicProvider(
        "secret",
        "claude-test",
        sdk_client=FakeAnthropicSdk(_anthropic_response(sdk_blocks, thinking_tokens=4)),
    )
    http = FakeHttpPost(_anthropic_http_payload(http_blocks, thinking_tokens=4))
    http_provider = luc.AnthropicProvider("secret", "claude-test", prefer_sdk=False, http_post=http)

    sdk_result = sdk_provider.generate(system_prompt="sys", messages=[], max_tokens=40)
    http_result = http_provider.generate(system_prompt="sys", messages=[], max_tokens=40)

    assert sdk_result == http_result


def test_sonnet_5_sdk_request_disables_thinking_without_sampling_params():
    sdk = FakeAnthropicSdk(_anthropic_response([types.SimpleNamespace(type="text", text="ok")]))
    provider = luc.AnthropicProvider("secret", "claude-sonnet-5", sdk_client=sdk)

    provider.generate(system_prompt="sys", messages=[], max_tokens=40)

    call = sdk.messages.calls[0]
    assert call["thinking"] == {"type": "disabled"}
    assert "temperature" not in call
    assert "top_p" not in call
    assert "top_k" not in call


def test_sonnet_5_raw_http_request_disables_thinking_without_sampling_params():
    http = FakeHttpPost(_anthropic_http_payload([{"type": "text", "text": "ok"}]))
    provider = luc.AnthropicProvider("secret", "claude-sonnet-5", prefer_sdk=False, http_post=http)

    provider.generate(system_prompt="sys", messages=[], max_tokens=40)

    payload = http.calls[0]["json"]
    assert payload["thinking"] == {"type": "disabled"}
    assert "temperature" not in payload
    assert "top_p" not in payload
    assert "top_k" not in payload


@pytest.mark.parametrize(
    "payload",
    [
        _chat_payload(content="", finish_reason="stop"),
        _chat_payload(content="   ", finish_reason="stop"),
        _chat_payload(content="truncated", finish_reason="length"),
        _chat_payload(content="tool", finish_reason="tool_calls", tool_calls=[{"id": "x"}]),
        {"choices": [], "usage": {"prompt_tokens": 1, "completion_tokens": 0}},
        {"choices": [{"finish_reason": "stop", "message": {}}], "usage": {"prompt_tokens": 1, "completion_tokens": 0}},
    ],
)
def test_chat_completions_incomplete_responses_fail_closed(payload):
    http = FakeHttpPost(payload)
    provider = luc.ChatCompletionsProvider(
        name="openrouter",
        base_url="https://openrouter.ai/api/v1",
        model="model",
        api_key="secret",
        http_post=http,
    )

    with pytest.raises(luc.ProviderResponseError):
        provider.generate(system_prompt="sys", messages=[], max_tokens=40)


def test_chat_completions_success_captures_finish_reason_and_tokens():
    http = FakeHttpPost(
        _chat_payload(
            content="complete",
            finish_reason="stop",
            usage={"prompt_tokens": 8, "completion_tokens": 5, "reasoning_tokens": 2},
        )
    )
    provider = luc.ChatCompletionsProvider(
        name="openai_compatible",
        base_url="http://localhost/v1",
        model="model",
        api_key="",
        http_post=http,
    )

    result = provider.generate(system_prompt="sys", messages=[], max_tokens=40)

    assert result.text == "complete"
    assert result.stop_reason == "stop"
    assert result.content_block_types == ["text"]
    assert result.input_tokens == 8
    assert result.output_tokens == 5
    assert result.thinking_tokens == 2


def test_provider_response_failure_does_not_append_history_or_ingest():
    bad = luc.ProviderResult(text="", stop_reason="end_turn", content_block_types=["thinking"])
    session, torment, provider = _preflighted(provider=FakeProvider(error=luc.ProviderResponseError("empty", bad)))

    outcome = session.run_turn("empty adapter output")

    assert outcome.failure_stage == "provider"
    assert outcome.assistant_text is None
    assert outcome.ingest_summary is None
    assert outcome.ingest_result is None
    assert outcome.ingest_call_count == 0
    assert torment.ingest_payloads == []
    assert session.history == []
    assert provider.calls


def test_no_thinking_text_enters_history_ingest_stdout_or_capture(capsys):
    hidden = "SECRET_THINKING_TEXT_SHOULD_NOT_APPEAR"
    result = luc.AnthropicProvider(
        "secret",
        "claude-test",
        sdk_client=FakeAnthropicSdk(
            _anthropic_response(
                [
                    types.SimpleNamespace(type="thinking", thinking=hidden),
                    types.SimpleNamespace(type="text", text="visible answer"),
                ]
            )
        ),
    ).generate(system_prompt="sys", messages=[], max_tokens=40)
    recorder = MemoryRecorder()
    session, torment, _provider = _preflighted(provider=FakeProvider(result=result), recorder=recorder)

    outcome = session.run_turn("hide thinking")

    assert outcome.ok
    blob = json.dumps(
        {
            "events": recorder.events,
            "history": session.history,
            "ingests": torment.ingest_payloads,
        },
        ensure_ascii=False,
    )
    captured = capsys.readouterr()
    assert hidden not in blob
    assert hidden not in captured.out
    assert hidden not in captured.err
    assert outcome.assistant_text == "visible answer"


def test_successful_provider_result_metadata_is_captured():
    recorder = MemoryRecorder()
    result = luc.ProviderResult(
        text="metadata ok",
        stop_reason="stop_sequence",
        content_block_types=["thinking", "text"],
        input_tokens=10,
        output_tokens=6,
        thinking_tokens=3,
    )
    session, _torment, _provider = _preflighted(provider=FakeProvider(result=result), recorder=recorder)

    outcome = session.run_turn("capture success")

    assert outcome.ok
    turn = _events_of(recorder, "turn")[-1]
    assert turn["provider_response"] == {
        "stop_reason": "stop_sequence",
        "content_block_types": ["thinking", "text"],
        "input_tokens": 10,
        "output_tokens": 6,
        "thinking_tokens": 3,
        "visible_text_present": True,
    }


def test_failed_provider_result_metadata_is_captured_safely():
    recorder = MemoryRecorder()
    result = luc.ProviderResult(
        text="partial",
        stop_reason="max_tokens",
        content_block_types=["text"],
        input_tokens=10,
        output_tokens=40,
        thinking_tokens=None,
    )
    session, torment, _provider = _preflighted(
        provider=FakeProvider(error=luc.ProviderResponseError("max_tokens", result)),
        recorder=recorder,
    )

    outcome = session.run_turn("capture failure")

    assert outcome.failure_stage == "provider"
    assert outcome.assistant_text is None
    assert outcome.ingest_summary is None
    assert outcome.ingest_result is None
    assert outcome.ingest_call_count == 0
    assert torment.ingest_payloads == []
    turn = _events_of(recorder, "turn")[-1]
    assert turn["provider_response"]["stop_reason"] == "max_tokens"
    assert turn["provider_response"]["visible_text_present"] is True
    assert "partial" not in json.dumps(turn["provider_response"], ensure_ascii=False)


def test_six_empty_response_failure_pattern_cannot_be_produced():
    result = luc.ProviderResult(text="", stop_reason="end_turn", content_block_types=["text"])
    provider = FakeProvider(error=luc.ProviderResponseError("empty", result))
    session, torment, _provider = _preflighted(provider=provider)

    outcomes = [session.run_turn(f"turn {i}") for i in range(6)]

    assert all(outcome.failure_stage == "provider" for outcome in outcomes)
    assert all(outcome.assistant_text is None for outcome in outcomes)
    assert all(outcome.ingest_result is None for outcome in outcomes)
    assert torment.ingest_payloads == []
    assert session.history == []


def test_repeated_successful_idempotent_creation_is_accepted_before_first_query():
    session, torment, _provider = _preflighted()
    session.run_turn("hello")

    names = _call_names(torment)
    assert names[:8] == [
        "health",
        "config",
        "debug_metrics",
        "profiles",
        "workspace_create",
        "agent_create",
        "agent_identity",
        "recent_index",
    ]
    assert names.index("workspace_create") < names.index("query")
    assert names.index("agent_create") < names.index("query")


@pytest.mark.parametrize("field", ["workspace", "agent"])
def test_creation_409_is_fatal_before_query_and_provider(field):
    error = luc.TormentHTTPError("POST", f"/{field}/create", 409)
    torment = FakeTorment(workspace_error=error if field == "workspace" else None, agent_error=error if field == "agent" else None)
    provider = FakeProvider()
    recorder = MemoryRecorder()
    session = _session(torment=torment, provider=provider, recorder=recorder)

    with pytest.raises(luc.TormentHTTPError):
        session.preflight()

    assert "query" not in _call_names(torment)
    assert "recent_index" not in _call_names(torment)
    assert provider.calls == []
    preflight = _events_of(recorder, "preflight")[-1]
    assert preflight["ok"] is False
    assert preflight["failure_stage"] == "preflight"
    assert "already_exists" not in json.dumps(preflight)


def test_empty_index_starts_at_zero_and_first_successful_ingest_uses_step_one():
    session, torment, _provider = _preflighted(torment=FakeTorment(recent=_recent()))

    assert session.current_step == 0
    outcome = session.run_turn("first turn")

    assert outcome.ok
    assert torment.ingest_payloads[0]["step"] == 1
    assert session.current_step == 1


def test_existing_recent_step_17_next_ingest_uses_18():
    session, torment, _provider = _preflighted(torment=FakeTorment(recent=_recent(17)))

    outcome = session.run_turn("continue")

    assert outcome.ok
    assert torment.ingest_payloads[0]["step"] == 18
    assert session.current_step == 18


def test_a0_stored_ingest_capture_retains_safe_outcome_metadata():
    recorder = MemoryRecorder()
    response = _ingest_response(
        eid=202,
        reason="stored cleanly",
        hidden_reasoning="do not retain",
        raw_internal_result={"do": "not retain"},
        provider_internals={"do": "not retain"},
        api_key="sk-test-secret",
        embedding=[0.1, 0.2],
    )
    session, _torment, _provider = _preflighted(
        torment=FakeTorment(ingest_response=response),
        recorder=recorder,
    )

    outcome = session.run_turn("capture stored metadata")

    assert outcome.ok
    turn = _events_of(recorder, "turn")[-1]
    ingest = turn["ingest_result"]
    assert turn["ingest_outcome"] == luc.INGEST_OUTCOME_STORED
    assert ingest["ingest_outcome"] == luc.INGEST_OUTCOME_STORED
    assert ingest["stored"] is True
    assert ingest["reinforced"] is False
    assert ingest["eid"] == 202
    assert ingest["path"] == "fast"
    assert ingest["escalated"] is False
    assert ingest["result_code"] == "stored"
    assert ingest["decision_code"] == "fast_allowed"
    assert ingest["reason"] == "stored cleanly"
    forbidden = json.dumps(ingest, ensure_ascii=False)
    assert "hidden_reasoning" not in forbidden
    assert "raw_internal_result" not in forbidden
    assert "provider_internals" not in forbidden
    assert "sk-test-secret" not in forbidden
    assert "embedding" not in ingest


def test_a0_reinforced_ingest_capture_is_distinct_from_new_store():
    recorder = MemoryRecorder()
    session, _torment, _provider = _preflighted(
        torment=FakeTorment(
            ingest_response=_ingest_response(
                stored=False,
                reinforced=True,
                eid=303,
                result_code="reinforced",
            )
        ),
        recorder=recorder,
    )

    outcome = session.run_turn("capture reinforcement")

    assert outcome.ok
    turn = _events_of(recorder, "turn")[-1]
    ingest = turn["ingest_result"]
    assert turn["ingest_outcome"] == luc.INGEST_OUTCOME_REINFORCED
    assert ingest["ingest_outcome"] == luc.INGEST_OUTCOME_REINFORCED
    assert ingest["stored"] is False
    assert ingest["reinforced"] is True
    assert ingest["eid"] == 303


def test_a0_explicit_non_write_capture_is_ingest_not_stored():
    recorder = MemoryRecorder()
    session, _torment, _provider = _preflighted(
        torment=FakeTorment(
            ingest_response=_ingest_response(
                stored=False,
                reinforced=False,
                eid=None,
                path="full",
                escalated=True,
                result_code="cognition",
                decision_code="escalated_full",
                reason="handled without durable write",
            )
        ),
        recorder=recorder,
    )

    outcome = session.run_turn("capture explicit non-write")

    assert outcome.ok
    turn = _events_of(recorder, "turn")[-1]
    ingest = turn["ingest_result"]
    assert turn["ingest_outcome"] == luc.INGEST_OUTCOME_NOT_STORED
    assert ingest["ingest_outcome"] == luc.INGEST_OUTCOME_NOT_STORED
    assert ingest["stored"] is False
    assert ingest["reinforced"] is False
    assert ingest["path"] == "full"
    assert ingest["escalated"] is True
    assert ingest["result_code"] == "cognition"
    assert ingest["decision_code"] == "escalated_full"


def test_a0_generic_http_success_without_outcome_evidence_is_unknown():
    recorder = MemoryRecorder()
    session, torment, _provider = _preflighted(
        torment=FakeTorment(recent=_recent(4), ingest_response={"ok": True, "status": "ok"}),
        recorder=recorder,
    )

    outcome = session.run_turn("generic success")

    assert outcome.ok
    assert session.current_step == 5
    assert torment.ingest_payloads[0]["step"] == 5
    turn = _events_of(recorder, "turn")[-1]
    ingest = turn["ingest_result"]
    assert turn["ingest_outcome"] == luc.INGEST_OUTCOME_UNKNOWN
    assert ingest["ingest_outcome"] == luc.INGEST_OUTCOME_UNKNOWN
    assert "stored" not in ingest
    assert "reinforced" not in ingest


def test_a0_non_mapping_ingest_response_does_not_break_turn_capture():
    class NonMappingIngestTorment(FakeTorment):
        def ingest(self, payload):
            self.calls.append(("ingest", copy.deepcopy(payload)))
            self.ingest_payloads.append(copy.deepcopy(payload))
            return []

    recorder = MemoryRecorder()
    torment = NonMappingIngestTorment(recent=_recent(4))
    provider = FakeProvider(reply="visible after non-mapping ingest")
    session, torment, provider = _preflighted(
        torment=torment,
        provider=provider,
        recorder=recorder,
    )

    outcome = session.run_turn("non-mapping ingest response")

    assert outcome.ok
    assert outcome.assistant_text == "visible after non-mapping ingest"
    assert len(provider.calls) == 1
    assert len(torment.ingest_payloads) == 1
    assert session.current_step == 5
    assert session.history == [
        {"role": "user", "content": "non-mapping ingest response"},
        {"role": "assistant", "content": "visible after non-mapping ingest"},
    ]
    turn = _events_of(recorder, "turn")[-1]
    assert turn["assistant_text"] == "visible after non-mapping ingest"
    assert turn["ingest_call_count"] == 1
    assert turn["current_step"] == 5
    assert "ingest_outcome" not in turn
    assert turn["ingest_result"].get("ingest_outcome") is None
    assert turn["ingest_result"].get("stored") is not True
    assert turn["ingest_result"].get("reinforced") is not True
    assert turn["ingest_result"].get("ingest_outcome") != luc.INGEST_OUTCOME_NOT_STORED


def test_ingest_observability_does_not_change_arguments_or_step_advancement():
    def run(ingest_response):
        torment = FakeTorment(ingest_response=ingest_response)
        provider = FakeProvider(reply="same reply")
        session = _session(torment=torment, provider=provider, recorder=MemoryRecorder())
        session.preflight()
        session.run_turn("same input")
        return (
            copy.deepcopy(torment.ingest_payloads),
            copy.deepcopy(provider.calls),
            session.current_step,
        )

    stored_ingests, stored_provider, stored_step = run(_ingest_response())
    unknown_ingests, unknown_provider, unknown_step = run({"ok": True, "status": "ok"})

    assert stored_ingests == unknown_ingests
    assert stored_provider == unknown_provider
    assert stored_step == unknown_step == 1


def test_failed_ingest_does_not_consume_step_and_next_turn_reuses_it():
    torment = FakeTorment(recent=_recent(17), ingest_error=[RuntimeError("down"), None])
    session, torment, _provider = _preflighted(torment=torment)

    first = session.run_turn("first")
    second = session.run_turn("second")

    assert first.failure_stage == "ingest"
    assert first.assistant_text is not None
    assert session.current_step == 18
    assert [payload["step"] for payload in torment.ingest_payloads] == [18, 18]
    assert second.ok


def test_epoch_scale_steps_are_not_generated_internally():
    session, torment, _provider = _preflighted(torment=FakeTorment(recent=_recent()))
    session.run_turn("small step")

    assert torment.ingest_payloads[0]["step"] == 1
    assert torment.ingest_payloads[0]["step"] < 1_000_000
    assert "time.time" not in MODULE_PATH.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "recent",
    [
        {"ok": False, "results": [], "detail": "SQLite index not available"},
        {"ok": True, "count": 1},
        _recent(malformed=True),
        {"ok": True, "results": ["bad"], "count": 1},
    ],
)
def test_unavailable_or_malformed_index_response_fails_preflight(recent):
    provider = FakeProvider()
    torment = FakeTorment(recent=recent)
    session = _session(torment=torment, provider=provider)

    with pytest.raises(luc.PreflightError):
        session.preflight()

    assert provider.calls == []
    assert "query" not in _call_names(torment)


def test_healthy_sentence_transformer_configuration_passes_preflight():
    session, _torment, _provider = _preflighted(torment=FakeTorment(health=_health()))
    assert session.preflight_ok


@pytest.mark.parametrize(
    "health",
    [
        _health(embedder={"provider": "hash", "model": "", "dim": 64, "cache_size": 0}, embedder_degraded=True),
        _health(embedder={"provider": "st", "model": "m", "dim": 0, "cache_size": 0}),
        _health(embedder={"provider": "st", "model": "m", "cache_size": 0}),
        _health(requested_embedder={"provider": "st", "model": "m", "strict": False}),
        _health(requested_embedder={"provider": "st", "model": "m"}),
    ],
)
def test_embedder_health_failures_abort_before_query_or_provider(health):
    torment = FakeTorment(health=health)
    provider = FakeProvider()
    session = _session(torment=torment, provider=provider)

    with pytest.raises(luc.PreflightError):
        session.preflight()

    assert _call_names(torment) == ["health"]
    assert provider.calls == []


@pytest.mark.parametrize(
    "identity",
    [
        _identity(seed_id="wrong"),
        _identity(character_name="Not Eira"),
        _identity(seed_text="same id, different text"),
    ],
)
def test_identity_mismatches_abort(identity):
    torment = FakeTorment(identity=identity)
    provider = FakeProvider()
    session = _session(torment=torment, provider=provider)

    with pytest.raises(luc.PreflightError):
        session.preflight()

    assert "recent_index" not in _call_names(torment)
    assert "query" not in _call_names(torment)
    assert provider.calls == []


def test_identity_missing_seed_text_fails_closed_with_safe_keys():
    identity = _identity()
    del identity["seed"]["seed_text"]
    session = _session(torment=FakeTorment(identity=identity), provider=FakeProvider())

    with pytest.raises(luc.PreflightError) as exc:
        session.preflight()

    msg = str(exc.value)
    assert "seed_text" in msg
    assert "observed seed keys" in msg
    assert _character().seed_text not in msg


def test_exact_identity_match_records_hashes_not_seed_text():
    recorder = MemoryRecorder()
    session, _torment, _provider = _preflighted(recorder=recorder)

    preflight = _events_of(recorder, "preflight")[-1]
    identity = preflight["identity"]
    assert identity["seed_id"] == luc.EXPECTED_SEED_ID
    assert identity["character_name"] == luc.EXPECTED_CHARACTER_NAME
    assert identity["local_seed_text_sha256"] == identity["returned_seed_text_sha256"]
    assert _character().seed_text not in json.dumps(preflight, ensure_ascii=False)
    assert session.current_step == preflight["resumed_step"]


def test_prompt_uses_torment_seed_preamble_but_not_local_seed_text():
    preamble = "This is the TORMENT-returned preamble."
    session, _torment, provider = _preflighted(torment=FakeTorment(query_response=_query_response(seed_preamble=preamble)))

    session.run_turn("prompt fidelity")
    system_prompt = provider.calls[0]["system_prompt"]

    assert preamble in system_prompt
    assert _character().seed_text not in system_prompt


def test_query_diagnostics_are_requested_and_captured_with_real_keys():
    recorder = MemoryRecorder()
    session, torment, _provider = _preflighted(recorder=recorder)

    session.run_turn("diagnostics")

    query_payload = torment.query_payloads[0]
    assert query_payload["explain"] is True
    assert query_payload["continuity_debug"] is True
    turn = _events_of(recorder, "turn")[-1]
    captured_hit = turn["query_response"]["results"][0]
    explain = captured_hit["explain"]
    assert explain["memory_plan_lane"] == "core"
    assert explain["srg_total_multiplier"] == 1.0
    assert explain["continuity_total_adjustment"] == 0.15
    assert "lane" not in explain
    assert "srg_multiplier" not in explain
    assert "continuity_bonus" not in explain
    assert "srg_band" not in explain
    assert explain["weights"] == {"alpha": 0.35, "beta": 0.1, "gamma": 0.2, "delta": 0.3}
    assert turn["query_response"]["continuity_debug"]["mode"] == "character_continuity"
    char_ctx = turn["query_response"]["character_context"]
    assert char_ctx["relational_count"] == 3
    assert char_ctx["tier_breakdown"] == {"core": 1, "relational": 3, "situational": 0}
    assert char_ctx["drift_direction"] == "stable"
    assert char_ctx["spirit_return_summary"] == "none"


def test_preflight_endpoint_allowlists_match_production_shapes():
    recorder = MemoryRecorder()
    _preflighted(recorder=recorder)

    preflight = _events_of(recorder, "preflight")[-1]
    health = preflight["health"]
    assert health["embedder"]["provider"] == "st"
    assert health["requested_embedder"]["strict"] is True
    assert health["embedder_degraded"] is False
    assert health["embedder_error"] == ""

    metrics = preflight["metrics"]
    assert set(["workspace_id", "agent_id", "features", "agents", "domains", "collective"]).issubset(metrics)
    assert metrics["features"] == {
        "compress_enable": False,
        "hivemind_enable": False,
        "srg_enable": False,
        "character_enable": True,
        "checkpoint_enable": True,
    }
    assert "counts" not in metrics
    assert "memory" not in metrics
    assert "requests" not in metrics

    config = preflight["config"]
    assert "TORMENT_DATA_DIR" in config["effective"]
    assert "TORMENT_EMBED_PROVIDER" in config["effective"]
    assert "TORMENT_CHARACTER_ENABLE" in config["effective"]
    assert "TORMENT_AFFECT_ENABLE" in config["effective"]
    assert "TORMENT_MOOD_DRIFT_ENABLE" in config["effective"]
    assert "TORMENT_MOOD_SPIRAL_ENABLE" in config["effective"]
    assert "TORMENT_ID_ANCHOR_ENABLE" in config["effective"]
    assert "TORMENT_ROLE_ENABLE" in config["effective"]
    assert "TORMENT_THREAD_WINDOW_STEPS" in config["effective"]
    assert "UNRELATED" not in config["effective"]


def test_capture_disabled_and_enabled_leave_requests_and_provider_inputs_identical():
    def run(recorder):
        torment = FakeTorment()
        provider = FakeProvider(reply="same reply")
        session = _session(torment=torment, provider=provider, recorder=recorder)
        session.preflight()
        session.run_turn("same input")
        return copy.deepcopy(torment.calls), copy.deepcopy(provider.calls)

    disabled_calls, disabled_provider = run(luc.JsonlRecorder(path=None, enabled=False))
    enabled_calls, enabled_provider = run(MemoryRecorder())

    assert enabled_calls == disabled_calls
    assert enabled_provider == disabled_provider


def test_recorder_failure_does_not_retry_or_suppress_calls(capsys):
    recorder = FailingRecorder()
    torment = FakeTorment()
    provider = FakeProvider()
    session = _session(torment=torment, provider=provider, recorder=recorder)

    session.preflight()
    outcome = session.run_turn("continue normally")

    assert outcome.ok
    assert len(torment.query_payloads) == 1
    assert len(provider.calls) == 1
    assert len(torment.ingest_payloads) == 1
    assert recorder.record_calls == 1
    assert recorder.disabled
    assert recorder.warned
    captured = capsys.readouterr()
    assert "sk-test-secret" not in captured.out
    assert "sk-test-secret" not in captured.err


def test_provider_failure_does_not_ingest_and_removes_pending_user():
    session, torment, provider = _preflighted(provider=FakeProvider(error=RuntimeError("provider down")))

    outcome = session.run_turn("this should not be ingested")

    assert outcome.failure_stage == "provider"
    assert len(provider.calls) == 1
    assert torment.ingest_payloads == []
    assert session.history == []


def test_query_failure_does_not_call_provider_or_ingest():
    torment = FakeTorment(query_error=RuntimeError("query down"))
    provider = FakeProvider()
    session = _session(torment=torment, provider=provider)
    session.preflight()

    outcome = session.run_turn("no memory")

    assert outcome.failure_stage == "query"
    assert provider.calls == []
    assert torment.ingest_payloads == []


def test_ingest_failure_preserves_visible_response_and_step():
    recorder = MemoryRecorder()
    torment = FakeTorment(recent=_recent(4), ingest_error=RuntimeError("ingest down"))
    provider = FakeProvider(reply="visible response")
    session = _session(torment=torment, provider=provider, recorder=recorder)
    session.preflight()

    outcome = session.run_turn("hello")

    assert outcome.failure_stage == "ingest"
    assert outcome.assistant_text == "visible response"
    assert outcome.ingest_summary is not None
    assert session.current_step == 4
    turn = _events_of(recorder, "turn")[-1]
    assert turn["failure_stage"] == "ingest"
    assert turn["ingest_outcome"] == luc.INGEST_OUTCOME_TRANSPORT_OR_SERVICE_FAILURE
    assert turn["assistant_text"] == "visible response"
    assert turn["ingest_summary"] == outcome.ingest_summary
    assert turn["ingest_result"] is None
    assert turn["current_step"] == 4


def test_dotenv_never_overrides_existing_values_even_empty():
    env = {"TORMENT_CHAT_PROVIDER": "anthropic", "TORMENT_CHAT_API_KEY": ""}
    with tempfile.TemporaryDirectory() as tmp:
        dot_env = Path(tmp) / ".env"
        dot_env.write_text(
            "TORMENT_CHAT_PROVIDER=openrouter\n"
            "TORMENT_CHAT_MODEL=from-file\n"
            "TORMENT_CHAT_API_KEY=from-file-secret\n",
            encoding="utf-8",
        )
        loaded = luc.load_dotenv_safely(paths=[dot_env], environ=env)

    assert loaded
    assert env["TORMENT_CHAT_PROVIDER"] == "anthropic"
    assert env["TORMENT_CHAT_MODEL"] == "from-file"
    assert env["TORMENT_CHAT_API_KEY"] == ""


def test_api_keys_do_not_appear_in_capture_requests_or_provider_inputs(capsys):
    secret = "sk-test-secret"
    env = {
        "ANTHROPIC_API_KEY": secret,
        "OPENROUTER_API_KEY": "or-test-secret",
        "TORMENT_CHAT_API_KEY": "local-test-secret",
    }
    query_response = _query_response()
    query_response["results"][0]["summary"] = f"memory mentions {secret}"
    query_response["character_context"]["recommendations"] = [f"avoid {secret}"]
    recorder = MemoryRecorder()
    torment = FakeTorment(query_response=query_response)
    provider = FakeProvider(reply=f"reply mentions {secret}")
    session = _session(torment=torment, provider=provider, recorder=recorder, environ=env)
    session.preflight()

    outcome = session.run_turn(f"user typed {secret}")

    assert secret not in json.dumps(recorder.events, ensure_ascii=False)
    assert secret not in json.dumps(torment.query_payloads, ensure_ascii=False)
    assert secret not in json.dumps(torment.ingest_payloads, ensure_ascii=False)
    assert secret not in json.dumps(provider.calls, ensure_ascii=False)
    assert secret not in (outcome.assistant_text or "")
    captured = capsys.readouterr()
    assert secret not in captured.out
    assert secret not in captured.err


def test_prompt_hash_matches_exact_provider_system_prompt_bytes():
    recorder = MemoryRecorder()
    session, _torment, provider = _preflighted(recorder=recorder)
    session.run_turn("hash this prompt")

    provider_prompt = provider.calls[0]["system_prompt"]
    turn = _events_of(recorder, "turn")[-1]
    expected = hashlib.sha256(provider_prompt.encode("utf-8")).hexdigest()
    assert turn["rendered_system_prompt_sha256"] == expected
    assert turn["rendered_system_prompt"] == provider_prompt


def test_session_files_use_exclusive_creation():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "capture.jsonl"
        recorder = luc.JsonlRecorder(path=path, enabled=True)
        recorder.close()

        with pytest.raises(FileExistsError):
            luc.JsonlRecorder(path=path, enabled=True)


def test_provider_selection_and_model_resolution():
    anthropic_model = luc.build_provider_from_env(
        {"TORMENT_CHAT_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": "a-key", "TORMENT_CHAT_MODEL": "claude-test"}
    )
    anthropic_legacy = luc.build_provider_from_env(
        {"TORMENT_CHAT_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": "a-key", "CLAUDE_MODEL": "claude-env"}
    )
    openrouter_model = luc.build_provider_from_env(
        {"TORMENT_CHAT_PROVIDER": "openrouter", "OPENROUTER_API_KEY": "or-key", "TORMENT_CHAT_MODEL": "gemini-test"}
    )
    openrouter_legacy = luc.build_provider_from_env(
        {"TORMENT_CHAT_PROVIDER": "openrouter", "OPENROUTER_API_KEY": "or-key", "OPENROUTER_MODEL": "router-env"}
    )
    local = luc.build_provider_from_env(
        {
            "TORMENT_CHAT_PROVIDER": "openai_compatible",
            "TORMENT_CHAT_BASE_URL": "http://127.0.0.1:11434/v1",
            "TORMENT_CHAT_MODEL": "local-test",
            "TORMENT_CHAT_API_KEY": "",
        }
    )

    assert anthropic_model.model == "claude-test"
    assert anthropic_legacy.model == "claude-env"
    assert openrouter_model.model == "gemini-test"
    assert openrouter_legacy.model == "router-env"
    assert local.name == "openai_compatible"
    assert local.api_key == ""


@pytest.mark.parametrize(
    "env",
    [
        {"TORMENT_CHAT_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": "a-key"},
        {"TORMENT_CHAT_PROVIDER": "openrouter", "OPENROUTER_API_KEY": "or-key"},
        {
            "TORMENT_CHAT_PROVIDER": "openai_compatible",
            "TORMENT_CHAT_BASE_URL": "ftp://bad",
            "TORMENT_CHAT_MODEL": "m",
        },
    ],
)
def test_provider_selection_clear_config_errors(env):
    with pytest.raises(luc.ProviderConfigError):
        luc.build_provider_from_env(env)


def test_provider_can_be_constructed_before_preflight_but_not_invoked():
    provider = FakeProvider()
    session = _session(provider=provider)

    with pytest.raises(luc.PreflightError):
        session.run_turn("too early")

    assert provider.calls == []

    failing_session = _session(torment=FakeTorment(health=_health(embedder_degraded=True)), provider=provider)
    with pytest.raises(luc.PreflightError):
        failing_session.preflight()
    assert provider.calls == []


def test_provider_model_changes_affect_metadata_only_not_torment_contract():
    def run(provider):
        torment = FakeTorment()
        recorder = MemoryRecorder()
        session = _session(torment=torment, provider=provider, recorder=recorder)
        session.preflight()
        session.run_turn("same request")
        return torment.calls, recorder.events

    torment_a, events_a = run(FakeProvider(name="anthropic", model="m-a", reply="same reply"))
    torment_b, events_b = run(FakeProvider(name="openrouter", model="m-b", reply="same reply"))

    assert torment_a == torment_b
    start_a = _events_of(type("R", (), {"events": events_a})(), "session_start")[0]
    start_b = _events_of(type("R", (), {"events": events_b})(), "session_start")[0]
    assert start_a["provider"] == "anthropic"
    assert start_b["provider"] == "openrouter"
    assert start_a["model"] == "m-a"
    assert start_b["model"] == "m-b"


@pytest.mark.parametrize(
    "stage,error_attr,expected_stage",
    [
        ("query", "query_error", "query_interrupted"),
        ("provider", None, "provider_interrupted"),
        ("ingest", "ingest_error", "ingest_interrupted"),
    ],
)
def test_keyboard_interrupt_records_incomplete_turn_and_stops_later_stages(stage, error_attr, expected_stage):
    recorder = MemoryRecorder()
    provider = FakeProvider(error=KeyboardInterrupt() if stage == "provider" else None)
    kwargs = {}
    if error_attr:
        kwargs[error_attr] = KeyboardInterrupt()
    torment = FakeTorment(recent=_recent(9), **kwargs)
    session = _session(torment=torment, provider=provider, recorder=recorder)
    session.preflight()

    with pytest.raises(KeyboardInterrupt):
        session.run_turn(f"interrupt {stage}")

    turn = _events_of(recorder, "turn")[-1]
    assert turn["failure_stage"] == expected_stage
    if stage == "query":
        assert provider.calls == []
        assert torment.ingest_payloads == []
    if stage == "provider":
        assert torment.ingest_payloads == []
        assert session.history == []
    if stage == "ingest":
        assert provider.calls
        assert session.current_step == 9


def test_no_retrieve_surface_exists_in_client_source_or_interface():
    source = MODULE_PATH.read_text(encoding="utf-8")
    assert '"/retrieve"' not in source
    assert not hasattr(luc.TormentHttpClient, "retrieve")
    assert not hasattr(luc.TormentClientProtocol, "retrieve")


def test_no_generic_recursive_capture_serialization_helpers():
    source = MODULE_PATH.read_text(encoding="utf-8")
    assert "_primitive" not in source
    assert "vars(" not in source
    assert "__dict__" not in source
    assert "repr(" not in source


def test_reference_clients_remain_lf_normalized_byte_identical():
    for rel, expected in REFERENCE_CLIENT_LF_HASHES.items():
        data = (ROOT / rel).read_bytes().replace(b"\r\n", b"\n")
        assert hashlib.sha256(data).hexdigest().upper() == expected
