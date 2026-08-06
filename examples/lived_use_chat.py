#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Focused A0 lived-use chat client for Eira Voss.

The provider object is constructed before preflight, but construction performs
no network I/O. The binding rule is stricter: no provider invocation happens
until preflight has verified health, configuration observability, workspace and
agent creation, exact seed identity, and the persistent ingest step baseline.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import subprocess
import sys
import textwrap
import uuid
from collections.abc import Mapping as MappingABC
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Protocol

import requests


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CHARACTER_PATH = Path(__file__).resolve().parent / "lived_use_character_v1.yaml"
DEFAULT_TORMENT_URL = "http://127.0.0.1:8787"
DEFAULT_TOP_K = 8
DEFAULT_MAX_HISTORY_MESSAGES = 40
DEFAULT_MAX_TOKENS = 1024
DEFAULT_QWEN_SEED = 20260805
QWEN_DEFAULT_TEMPERATURE = 0.7
QWEN_DEFAULT_TOP_P = 0.8
QWEN_DEFAULT_TOP_K = 20
QWEN_DEFAULT_MIN_P = 0.0

EXPECTED_WORKSPACE_ID = "lived_use_eira_voss_a0"
EXPECTED_AGENT_ID = "eira_voss"
EXPECTED_USER_NAME = "Hilmir"
EXPECTED_DOMAIN = "personal"
EXPECTED_SEED_ID = "eira_voss_lived_use_v1"
EXPECTED_CHARACTER_NAME = "Eira Voss"

CAPTURE_ENV = "TORMENT_LIVED_USE_CAPTURE"
CAPTURE_DIR = REPO_ROOT / "outputs" / "lived_use" / EXPECTED_WORKSPACE_ID

SYSTEM_PROMPT_TEMPLATE = textwrap.dedent(
    """\
    You are {character_name}.

    {character_context}

    {memory_context}

    {drift_note}
    """
)

TORMENT_ENV_ALLOWLIST = (
    "TORMENT_URL",
    "TORMENT_PROFILE",
    "TORMENT_DATA_DIR",
    "TORMENT_CHARACTER_ENABLE",
    "TORMENT_THINKING_ADVISORY",
    "TORMENT_SPINE_ENABLE",
    "TORMENT_IDENTITY_SENSITIVE",
    "TORMENT_COMPRESS_ENABLE",
    "TORMENT_ARCHIVE_RECALL",
    "TORMENT_LIVE_SOCIAL",
    "TORMENT_CONTEXTUAL_ABSTENTION",
    "TORMENT_SRG_ENABLE",
    "TORMENT_SRG_COGNITION",
    "TORMENT_HIVEMIND_ENABLE",
    "TORMENT_COGNITION_SHAPING_V2",
    "TORMENT_COGNITION_CORE_SHAPING_V1",
    "TORMENT_GEOMETRIC_MEMORY_SHAPING_V1",
    "TORMENT_GEOMETRIC_RELATIONAL_PROMINENCE_SHAPING_V1",
    "TORMENT_RELATIONAL_AMBIGUITY_PROMINENCE_V1",
    "TORMENT_AMBIGUITY_CONTEXT_DIVERSITY_V1",
    "TORMENT_PARTICIPATION_GUIDANCE_V1",
    "TORMENT_SQLITE_INDEX_ENABLE",
    "TORMENT_EMBED_PROVIDER",
    "TORMENT_EMBED_MODEL",
    "TORMENT_EMBED_DEVICE",
    "TORMENT_EMBED_STRICT",
    "TORMENT_TOP_K",
    "TORMENT_CHAT_PROVIDER",
    "TORMENT_CHAT_MODEL",
    "TORMENT_CHAT_MODEL_PATH",
    "TORMENT_CHAT_BASE_URL",
    "TORMENT_CHAT_QWEN_GREEDY",
    "TORMENT_CHAT_SEED",
    "TORMENT_TEST_CONDITION",
    "TORMENT_EXPECTED_DATA_DIR",
    "TORMENT_SERVER_LAUNCHER_PATH",
    "CLAUDE_MODEL",
    "OPENROUTER_MODEL",
    CAPTURE_ENV,
)

CONFIG_EFFECTIVE_KEYS = (
    "TORMENT_DATA_DIR",
    "TORMENT_PROFILE",
    "TORMENT_EMBED_PROVIDER",
    "TORMENT_EMBED_MODEL",
    "TORMENT_EMBED_DEVICE",
    "TORMENT_EMBED_STRICT",
    "TORMENT_CHARACTER_ENABLE",
    "TORMENT_CHARACTER_DRIFT_WINDOW_STEPS",
    "TORMENT_CHARACTER_CORRECTION_THRESHOLD",
    "TORMENT_CHARACTER_GRAVITY_STRENGTH",
    "TORMENT_CHARACTER_DRIFT_CHECK_EVERY",
    "TORMENT_AFFECT_ENABLE",
    "TORMENT_AFFECT_MATCH_BONUS",
    "TORMENT_AFFECT_MIN_CONF",
    "TORMENT_MOOD_DRIFT_ENABLE",
    "TORMENT_MOOD_DRIFT_MIN_CONF",
    "TORMENT_MOOD_DRIFT_MIN_GAP_STEPS",
    "TORMENT_MOOD_DRIFT_HALF_LIFE_DAYS",
    "TORMENT_MOOD_DRIFT_QUERY_BONUS",
    "TORMENT_MOOD_SPIRAL_ENABLE",
    "TORMENT_MOOD_SPIRAL_WINDOW_STEPS",
    "TORMENT_MOOD_SPIRAL_MIN_NEG_DRIFTS",
    "TORMENT_MOOD_SPIRAL_OLDER_THAN_STEPS",
    "TORMENT_MOOD_SPIRAL_PENALTY_MAX",
    "TORMENT_ID_ANCHOR_ENABLE",
    "TORMENT_ID_ANCHOR_MIN_COUNT",
    "TORMENT_ID_ANCHOR_MIN_GAP_STEPS",
    "TORMENT_ID_ANCHOR_MAX_EXAMPLES",
    "TORMENT_ID_ANCHOR_AFFECT_COUNT_MULT",
    "TORMENT_ID_ANCHOR_AFFECT_GAP_MULT",
    "TORMENT_ANCHOR_BOOST_TOPK",
    "TORMENT_ANCHOR_BOOST_REST_MULT",
    "TORMENT_ANCHOR_KEEP_PER_MOTIF",
    "TORMENT_ANCHOR_WEAK_MEMBER_MAX",
    "TORMENT_ANCHOR_WEAK_MIN_AGE_STEPS",
    "TORMENT_ROLE_ENABLE",
    "TORMENT_ROLE_EMA",
    "TORMENT_SELF_MEMORY_BONUS",
    "TORMENT_SELF_ANCHOR_BONUS",
    "TORMENT_THREAD_WINDOW_STEPS",
    "TORMENT_THREAD_WINDOW_BONUS",
    "TORMENT_CONTINUITY_DEBUG_TOP",
    "TORMENT_CONTINUITY_DEBUG_MAX_HITS",
)

METRICS_FEATURE_KEYS = (
    "compress_enable",
    "hivemind_enable",
    "srg_enable",
    "character_enable",
    "checkpoint_enable",
)

EXPLAIN_SCALAR_KEYS = (
    "sim",
    "strength",
    "recency_days",
    "motif_alignment",
    "contradiction_risk",
    "collective_discount",
    "tool_result_discount",
    "conflict_penalty",
    "conflict_status",
    "provenance_type",
    "self_thread_bonus",
    "self_anchor_bonus",
    "thread_window_bonus",
    "affect_match_bonus",
    "mood_drift_bonus",
    "mood_spiral_penalty",
    "continuity_total_adjustment",
    "srg_same_band_bonus",
    "srg_crystal_bonus",
    "srg_heartbeat_bonus",
    "srg_total_multiplier",
    "memory_plan_lane",
    "lane_weight",
    "lane_weight_applied",
)

EXPLAIN_WEIGHT_KEYS = ("alpha", "beta", "gamma", "delta")
CONTINUITY_FLAG_KEYS = (
    "self_thread",
    "thread_window",
    "identity_anchors",
    "affect_match",
    "mood_drift",
    "mood_spiral",
)
CONTINUITY_SUMMARY_KEYS = (
    "self_thread",
    "self_anchor",
    "thread_window",
    "affect_match",
    "mood_drift",
    "mood_spiral_penalty",
)
TOP_HIT_BONUS_KEYS = (
    "self_thread",
    "self_anchor",
    "thread_window",
    "affect_match",
    "mood_drift",
)

SECRET_ENV_NAMES = (
    "ANTHROPIC_API_KEY",
    "OPENROUTER_API_KEY",
    "TORMENT_CHAT_API_KEY",
)

HASH_FALLBACK_PROVIDERS = {"hash", "det", "deterministic"}


class PreflightError(RuntimeError):
    pass


class ProviderConfigError(RuntimeError):
    pass


class ProviderError(RuntimeError):
    pass


class TormentHTTPError(RuntimeError):
    def __init__(self, method: str, path: str, status_code: int):
        super().__init__(f"{method} {path} failed with HTTP {int(status_code)}")
        self.method = method
        self.path = path
        self.status_code = int(status_code)


@dataclass(frozen=True)
class CharacterSpec:
    workspace_id: str
    agent_id: str
    user_name: str
    domain: str
    seed: Dict[str, Any]

    @property
    def seed_id(self) -> str:
        return str(self.seed.get("seed_id", ""))

    @property
    def character_name(self) -> str:
        return str(self.seed.get("character_name", self.agent_id))

    @property
    def seed_text(self) -> str:
        return str(self.seed.get("seed_text", ""))


@dataclass
class TurnOutcome:
    turn_id: int
    assistant_text: Optional[str]
    failure_stage: Optional[str]
    provider_response: Optional["ProviderResult"]
    query_request: Optional[Dict[str, Any]]
    query_response: Optional[Dict[str, Any]]
    rendered_system_prompt: Optional[str]
    rendered_system_prompt_sha256: Optional[str]
    provider_messages: List[Dict[str, str]]
    ingest_summary: Optional[str]
    ingest_result: Optional[Dict[str, Any]]
    query_call_count: int
    retrieve_call_count: int
    ingest_call_count: int

    @property
    def ok(self) -> bool:
        return self.failure_stage is None


@dataclass
class CommandOutcome:
    handled: bool
    should_exit: bool
    message: str


class TormentClientProtocol(Protocol):
    def health(self) -> Dict[str, Any]: ...
    def config(self) -> Dict[str, Any]: ...
    def debug_metrics(self) -> Dict[str, Any]: ...
    def profiles(self) -> Dict[str, Any]: ...
    def workspace_create(self, workspace_id: str, domains: List[str]) -> Dict[str, Any]: ...
    def agent_create(self, workspace_id: str, agent_id: str, seed: Dict[str, Any]) -> Dict[str, Any]: ...
    def agent_identity(self, workspace_id: str, agent_id: str) -> Dict[str, Any]: ...
    def recent_index(self, workspace_id: str, agent_id: str, limit: int = 1) -> Dict[str, Any]: ...
    def thinking_debug(self, payload: Dict[str, Any]) -> Dict[str, Any]: ...
    def query(self, payload: Dict[str, Any]) -> Dict[str, Any]: ...
    def ingest(self, payload: Dict[str, Any]) -> Dict[str, Any]: ...
    def ingest_route_probe(self, payload: Dict[str, Any]) -> Dict[str, Any]: ...


class ChatProvider(Protocol):
    name: str
    model: str

    def generate(
        self,
        *,
        system_prompt: str,
        messages: List[Dict[str, str]],
        max_tokens: int,
    ) -> "ProviderResult": ...


@dataclass(frozen=True)
class ProviderResult:
    text: str
    stop_reason: Optional[str]
    content_block_types: List[str]
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    thinking_tokens: Optional[int] = None
    generation_parameters: Dict[str, Any] = field(default_factory=dict)

    @property
    def visible_text_present(self) -> bool:
        return bool(str(self.text).strip())


class ProviderResponseError(ProviderError):
    def __init__(self, message: str, result: ProviderResult):
        super().__init__(message)
        self.result = result


def utc_timestamp() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_utf8(text: str) -> str:
    return hashlib.sha256(str(text).encode("utf-8")).hexdigest()


def env_value(environ: Mapping[str, str], name: str, default: str = "") -> str:
    value = str(environ.get(name, "")).strip()
    return value if value else default


def is_truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("1", "true", "yes", "on")


def _secret_values(environ: Optional[Mapping[str, str]] = None) -> List[str]:
    env = environ or os.environ
    values: List[str] = []
    for name in SECRET_ENV_NAMES:
        value = str(env.get(name, "")).strip()
        if value:
            values.append(value)
    return values


def redact_known_secrets(text: str, environ: Optional[Mapping[str, str]] = None) -> str:
    out = str(text)
    for secret in _secret_values(environ):
        out = out.replace(secret, "[redacted-secret]")
    return out


def _is_secretish_key(key: str) -> bool:
    upper = key.upper()
    return (
        "SECRET" in upper
        or "PASSWORD" in upper
        or "API_KEY" in upper
        or upper in ("KEY", "TOKEN")
        or upper.endswith("_KEY")
        or upper.endswith("_TOKEN")
    )


def safe_scalar(value: Any, environ: Optional[Mapping[str, str]] = None) -> Any:
    if value is None:
        return None
    if isinstance(value, bool):
        return bool(value)
    if isinstance(value, int) and not isinstance(value, bool):
        return int(value)
    if isinstance(value, float):
        return float(value)
    if isinstance(value, str):
        return redact_known_secrets(value, environ)
    return None


def safe_string(value: Any, environ: Optional[Mapping[str, str]] = None) -> str:
    scalar = safe_scalar(value, environ)
    if scalar is None:
        return ""
    return str(scalar)


def safe_error(error: BaseException, environ: Optional[Mapping[str, str]] = None) -> str:
    return redact_known_secrets(str(error), environ)


def safe_int(value: Any) -> Optional[int]:
    if isinstance(value, bool) or value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def safe_float(value: Any) -> Optional[float]:
    if isinstance(value, bool) or value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def get_field(value: Any, key: str) -> Any:
    if isinstance(value, dict):
        return value.get(key)
    return getattr(value, key, None)


def safe_block_type(value: Any) -> str:
    scalar = safe_scalar(value)
    return str(scalar) if scalar is not None else ""


def usage_token(usage: Any, *keys: str) -> Optional[int]:
    for key in keys:
        value = get_field(usage, key)
        found = safe_int(value)
        if found is not None:
            return found
    return None


def safe_optional_string(value: Any) -> Optional[str]:
    scalar = safe_scalar(value)
    if scalar is None:
        return None
    return str(scalar)


def result_or_error(result: ProviderResult, accepted_stop_reasons: Iterable[str], provider_name: str) -> ProviderResult:
    accepted = {str(reason) for reason in accepted_stop_reasons}
    if not result.visible_text_present:
        raise ProviderResponseError(f"{provider_name} response contained no visible text", result)
    if result.stop_reason not in accepted:
        reason = result.stop_reason if result.stop_reason is not None else "<missing>"
        raise ProviderResponseError(f"{provider_name} response stopped with {reason}", result)
    return result


def scalar_fields(
    source: Mapping[str, Any],
    keys: Iterable[str],
    environ: Optional[Mapping[str, str]] = None,
) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for key in keys:
        if key in source:
            out[key] = safe_scalar(source.get(key), environ)
    return out


def scalar_list(values: Any, environ: Optional[Mapping[str, str]] = None) -> List[Any]:
    if not isinstance(values, list):
        return []
    out: List[Any] = []
    for value in values:
        scalar = safe_scalar(value, environ)
        if scalar is not None:
            out.append(scalar)
    return out


def safe_capture_value(value: Any, environ: Optional[Mapping[str, str]] = None) -> Any:
    scalar = safe_scalar(value, environ)
    if scalar is not None or value is None:
        return scalar
    if isinstance(value, MappingABC):
        return {
            safe_string(key, environ): safe_capture_value(item, environ)
            for key, item in value.items()
            if isinstance(key, str) and not _is_secretish_key(key)
        }
    if isinstance(value, (list, tuple, set)):
        return [
            item
            for item in (safe_capture_value(entry, environ) for entry in value)
            if item is not None
        ]
    return safe_string(value, environ)


def filtered_torment_env(environ: Optional[Mapping[str, str]] = None) -> Dict[str, str]:
    env = environ or os.environ
    out: Dict[str, str] = {}
    for key in TORMENT_ENV_ALLOWLIST:
        if key in env and not _is_secretish_key(key):
            out[key] = redact_known_secrets(str(env[key]), env)
    return out


def file_sha256_info(path: Optional[Path], environ: Optional[Mapping[str, str]] = None) -> Optional[Dict[str, Any]]:
    if path is None:
        return None
    p = Path(path)
    info: Dict[str, Any] = {"path": safe_string(str(p), environ), "exists": p.exists()}
    if not p.exists() or not p.is_file():
        info["sha256"] = None
        return info
    digest = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    info["sha256"] = digest.hexdigest()
    return info


def git_capture_snapshot(repo_root: Path = REPO_ROOT, environ: Optional[Mapping[str, str]] = None) -> Dict[str, Any]:
    def run_git(args: List[str]) -> Optional[str]:
        try:
            proc = subprocess.run(
                ["git"] + list(args),
                cwd=str(repo_root),
                text=True,
                capture_output=True,
                check=False,
                timeout=5,
            )
        except Exception:
            return None
        if proc.returncode != 0:
            return None
        return proc.stdout.strip()

    head = run_git(["rev-parse", "HEAD"])
    branch = run_git(["branch", "--show-current"])
    status = run_git(["status", "--short"])
    dirty_paths: List[str] = []
    if status:
        for line in status.splitlines():
            text = line.rstrip()
            if not text:
                continue
            path = text[3:] if len(text) > 3 else text
            if " -> " in path:
                path = path.split(" -> ", 1)[1]
            dirty_paths.append(safe_string(path.strip(), environ))
    return {
        "head": safe_scalar(head, environ),
        "branch": safe_scalar(branch, environ),
        "dirty_paths": dirty_paths,
    }


def normalized_path_string(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    return os.path.normcase(os.path.normpath(text))


def load_dotenv_safely(
    paths: Optional[Iterable[Path]] = None,
    environ: Optional[MutableMapping[str, str]] = None,
) -> List[str]:
    """Load KEY=value pairs without overriding existing variables.

    Deliberately empty existing values still win; `.env` may not refill them.
    """

    env = environ if environ is not None else os.environ
    candidates = list(paths) if paths is not None else [REPO_ROOT / ".env", Path.cwd() / ".env"]
    loaded: List[str] = []
    seen: set[Path] = set()
    for path in candidates:
        try:
            resolved = Path(path).resolve()
        except OSError:
            continue
        if resolved in seen or not resolved.exists() or not resolved.is_file():
            continue
        seen.add(resolved)
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
            loaded.append(str(resolved))
        except OSError:
            continue
    return loaded


def load_character_spec(path: Path = DEFAULT_CHARACTER_PATH) -> CharacterSpec:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        raw = yaml.safe_load(text)
    except ModuleNotFoundError:
        raw = json.loads(text)
    if not isinstance(raw, dict):
        raise ValueError(f"Character spec must be a mapping: {path}")
    seed = raw.get("seed")
    if not isinstance(seed, dict):
        raise ValueError(f"Character spec must contain a seed mapping: {path}")
    return CharacterSpec(
        workspace_id=str(raw.get("workspace_id", "")),
        agent_id=str(raw.get("agent_id", "")),
        user_name=str(raw.get("user_name", "")),
        domain=str(raw.get("domain", "")),
        seed={
            "seed_id": str(seed.get("seed_id", "")),
            "character_name": str(seed.get("character_name", "")),
            "seed_text": str(seed.get("seed_text", "")),
            "core_traits": list(seed.get("core_traits", [])) if isinstance(seed.get("core_traits"), list) else [],
        },
    )


def validate_a0_spec(spec: CharacterSpec) -> None:
    expected = {
        "workspace_id": EXPECTED_WORKSPACE_ID,
        "agent_id": EXPECTED_AGENT_ID,
        "user_name": EXPECTED_USER_NAME,
        "domain": EXPECTED_DOMAIN,
        "seed_id": EXPECTED_SEED_ID,
        "character_name": EXPECTED_CHARACTER_NAME,
    }
    actual = {
        "workspace_id": spec.workspace_id,
        "agent_id": spec.agent_id,
        "user_name": spec.user_name,
        "domain": spec.domain,
        "seed_id": spec.seed_id,
        "character_name": spec.character_name,
    }
    for key, expected_value in expected.items():
        if actual[key] != expected_value:
            raise ValueError(f"A0 character spec mismatch for {key}: {actual[key]}")


class TormentHttpClient:
    def __init__(self, base_url: str, timeout_s: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.timeout_s = float(timeout_s)
        self.session = requests.Session()

    def _url(self, path: str) -> str:
        if not path.startswith("/"):
            path = "/" + path
        return self.base_url + path

    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            response = self.session.post(self._url(path), json=payload, timeout=self.timeout_s)
        except requests.RequestException:
            raise RuntimeError(f"POST {path} failed before HTTP response") from None
        if response.status_code >= 400:
            raise TormentHTTPError("POST", path, response.status_code)
        return response.json()

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            response = self.session.get(self._url(path), params=params or {}, timeout=self.timeout_s)
        except requests.RequestException:
            raise RuntimeError(f"GET {path} failed before HTTP response") from None
        if response.status_code >= 400:
            raise TormentHTTPError("GET", path, response.status_code)
        return response.json()

    def health(self) -> Dict[str, Any]:
        return self._get("/health")

    def config(self) -> Dict[str, Any]:
        return self._get("/config")

    def debug_metrics(self) -> Dict[str, Any]:
        return self._get("/debug/metrics")

    def profiles(self) -> Dict[str, Any]:
        return self._get("/profiles")

    def workspace_create(self, workspace_id: str, domains: List[str]) -> Dict[str, Any]:
        return self._post("/workspace/create", {"workspace_id": workspace_id, "domains": list(domains)})

    def agent_create(self, workspace_id: str, agent_id: str, seed: Dict[str, Any]) -> Dict[str, Any]:
        return self._post(
            "/agent/create",
            {"workspace_id": workspace_id, "agent_id": agent_id, "seed": dict(seed)},
        )

    def agent_identity(self, workspace_id: str, agent_id: str) -> Dict[str, Any]:
        return self._get(f"/agent/{agent_id}/identity", {"workspace_id": workspace_id})

    def recent_index(self, workspace_id: str, agent_id: str, limit: int = 1) -> Dict[str, Any]:
        return self._get(f"/index/{workspace_id}/{agent_id}/recent", {"limit": int(limit)})

    def thinking_debug(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._post("/thinking/debug", payload)

    def query(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._post("/agent/query", payload)

    def ingest(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._post("/agent/ingest", payload)

    def ingest_route_probe(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._post("/agent/ingest/route_probe", payload)


class AnthropicProvider:
    name = "anthropic"
    ACCEPTED_STOP_REASONS = ("end_turn", "stop_sequence")

    def __init__(
        self,
        api_key: str,
        model: str,
        *,
        sdk_client: Any = None,
        prefer_sdk: bool = True,
        http_post: Any = None,
    ):
        self.api_key = api_key
        self.model = model
        self._sdk_client = sdk_client
        self._http_post = http_post or requests.post
        if self._sdk_client is None and prefer_sdk:
            try:
                import anthropic  # type: ignore

                self._sdk_client = anthropic.Anthropic(api_key=api_key)
            except ImportError:
                self._sdk_client = None

    def _thinking_config(self) -> Optional[Dict[str, str]]:
        if self.model.strip() == "claude-sonnet-5":
            return {"type": "disabled"}
        return None

    def generation_parameters(self, max_tokens: int) -> Dict[str, Any]:
        return {
            "provider": self.name,
            "model": self.model,
            "max_tokens": int(max_tokens),
            "thinking": self._thinking_config(),
            "random_seed": None,
            "random_seed_supported": False,
            "randomness": "provider_controlled",
            "temperature": "provider_default_unset",
            "top_p": "provider_default_unset",
            "top_k": "provider_default_unset",
        }

    def _parse_response(self, response: Any, generation_parameters: Optional[Dict[str, Any]] = None) -> ProviderResult:
        content = get_field(response, "content")
        if not isinstance(content, list):
            content = []
        block_types: List[str] = []
        text_parts: List[str] = []
        for block in content:
            block_type = safe_block_type(get_field(block, "type"))
            block_types.append(block_type)
            if block_type == "text":
                text_value = get_field(block, "text")
                if isinstance(text_value, str):
                    text_parts.append(text_value)
        usage = get_field(response, "usage")
        result = ProviderResult(
            text="".join(text_parts),
            stop_reason=safe_optional_string(get_field(response, "stop_reason")),
            content_block_types=block_types,
            input_tokens=usage_token(usage, "input_tokens"),
            output_tokens=usage_token(usage, "output_tokens"),
            thinking_tokens=usage_token(usage, "thinking_tokens", "reasoning_tokens"),
            generation_parameters=generation_parameters or {},
        )
        return result_or_error(result, self.ACCEPTED_STOP_REASONS, self.name)

    def generate(
        self,
        *,
        system_prompt: str,
        messages: List[Dict[str, str]],
        max_tokens: int,
    ) -> ProviderResult:
        thinking = self._thinking_config()
        generation_parameters = self.generation_parameters(max_tokens)
        if self._sdk_client is not None:
            kwargs: Dict[str, Any] = {
                "model": self.model,
                "max_tokens": int(max_tokens),
                "system": system_prompt,
                "messages": messages,
            }
            if thinking is not None:
                kwargs["thinking"] = thinking
            try:
                response = self._sdk_client.messages.create(**kwargs)
            except Exception:
                raise ProviderError("anthropic SDK request failed") from None
            return self._parse_response(response, generation_parameters)

        payload: Dict[str, Any] = {
            "model": self.model,
            "max_tokens": int(max_tokens),
            "system": system_prompt,
            "messages": messages,
        }
        if thinking is not None:
            payload["thinking"] = thinking
        try:
            response = self._http_post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json=payload,
                timeout=60,
            )
        except requests.RequestException:
            raise ProviderError("anthropic request failed before HTTP response") from None
        if response.status_code >= 400:
            raise ProviderError(f"anthropic request failed with HTTP {response.status_code}")
        return self._parse_response(response.json(), generation_parameters)


class ChatCompletionsProvider:
    ACCEPTED_STOP_REASONS = ("stop",)

    def __init__(
        self,
        *,
        name: str,
        base_url: str,
        model: str,
        api_key: Optional[str],
        http_post: Any = None,
    ):
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key or ""
        self._http_post = http_post or requests.post

    def _missing_result(self, stop_reason: Optional[str] = None, content_block_types: Optional[List[str]] = None) -> ProviderResult:
        return ProviderResult(
            text="",
            stop_reason=stop_reason,
            content_block_types=content_block_types or [],
            input_tokens=None,
            output_tokens=None,
            thinking_tokens=None,
        )

    def generation_parameters(self, max_tokens: int) -> Dict[str, Any]:
        return {
            "provider": self.name,
            "model": self.model,
            "max_tokens": int(max_tokens),
            "temperature": "provider_default_unset",
            "top_p": "provider_default_unset",
            "top_k": "provider_default_unset",
            "random_seed": None,
            "random_seed_supported": False,
        }

    def _parse_response(self, data: Any, generation_parameters: Optional[Dict[str, Any]] = None) -> ProviderResult:
        if not isinstance(data, dict):
            raise ProviderResponseError(f"{self.name} response was malformed", self._missing_result())
        choices = data.get("choices")
        usage = data.get("usage")
        if not isinstance(choices, list) or not choices:
            raise ProviderResponseError(
                f"{self.name} response contained no choices",
                ProviderResult(
                    text="",
                    stop_reason=None,
                    content_block_types=[],
                    input_tokens=usage_token(usage, "prompt_tokens", "input_tokens"),
                    output_tokens=usage_token(usage, "completion_tokens", "output_tokens"),
                    thinking_tokens=usage_token(usage, "reasoning_tokens", "thinking_tokens"),
                ),
            )
        first = choices[0]
        if not isinstance(first, dict):
            raise ProviderResponseError(f"{self.name} choice was malformed", self._missing_result())
        finish_reason = safe_optional_string(first.get("finish_reason"))
        message = first.get("message")
        block_types: List[str] = []
        text = ""
        if isinstance(message, dict):
            if isinstance(message.get("content"), str):
                block_types.append("text")
                text = message["content"]
            if isinstance(message.get("tool_calls"), list) and message.get("tool_calls"):
                block_types.append("tool_calls")
        result = ProviderResult(
            text=text,
            stop_reason=finish_reason,
            content_block_types=block_types,
            input_tokens=usage_token(usage, "prompt_tokens", "input_tokens"),
            output_tokens=usage_token(usage, "completion_tokens", "output_tokens"),
            thinking_tokens=usage_token(usage, "reasoning_tokens", "thinking_tokens"),
            generation_parameters=generation_parameters or {},
        )
        return result_or_error(result, self.ACCEPTED_STOP_REASONS, self.name)

    def generate(
        self,
        *,
        system_prompt: str,
        messages: List[Dict[str, str]],
        max_tokens: int,
    ) -> ProviderResult:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        payload_messages = [{"role": "system", "content": system_prompt}] + list(messages)
        generation_parameters = self.generation_parameters(max_tokens)
        try:
            response = self._http_post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json={
                    "model": self.model,
                    "messages": payload_messages,
                    "max_tokens": int(max_tokens),
                },
                timeout=60,
            )
        except requests.RequestException:
            raise ProviderError(f"{self.name} request failed before HTTP response") from None
        if response.status_code >= 400:
            raise ProviderError(f"{self.name} request failed with HTTP {response.status_code}")
        return self._parse_response(response.json(), generation_parameters)


def _first_token_sequence(token_ids: Any) -> List[int]:
    if hasattr(token_ids, "tolist"):
        token_ids = token_ids.tolist()
    if isinstance(token_ids, tuple):
        token_ids = list(token_ids)
    if isinstance(token_ids, list) and token_ids and isinstance(token_ids[0], (list, tuple)):
        return [int(token) for token in token_ids[0]]
    if isinstance(token_ids, list):
        return [int(token) for token in token_ids]
    return [int(token) for token in list(token_ids)]


def _token_sequence_length(token_ids: Any) -> int:
    shape = getattr(token_ids, "shape", None)
    if shape:
        return int(shape[-1])
    return len(_first_token_sequence(token_ids))


def _token_id_values(value: Any) -> List[int]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        out: List[int] = []
        for item in value:
            found = safe_int(item)
            if found is not None:
                out.append(found)
        return out
    found = safe_int(value)
    return [found] if found is not None else []


class LocalQwenProvider:
    name = "local_qwen"
    ACCEPTED_STOP_REASONS = ("stop", "length")

    def __init__(
        self,
        *,
        model: str,
        model_path: Path,
        do_sample: bool = True,
        temperature: float = QWEN_DEFAULT_TEMPERATURE,
        top_p: float = QWEN_DEFAULT_TOP_P,
        top_k: int = QWEN_DEFAULT_TOP_K,
        min_p: float = QWEN_DEFAULT_MIN_P,
        seed: int = DEFAULT_QWEN_SEED,
        torch_module: Any = None,
        tokenizer_cls: Any = None,
        model_cls: Any = None,
    ):
        self.model = str(model)
        self.model_path = Path(model_path)
        self.do_sample = bool(do_sample)
        self.temperature = float(temperature)
        self.top_p = float(top_p)
        self.top_k = int(top_k)
        self.min_p = float(min_p)
        self.seed = int(seed)
        self._torch_module = torch_module
        self._tokenizer_cls = tokenizer_cls
        self._model_cls = model_cls
        self._tokenizer: Any = None
        self._model: Any = None
        self._last_eos_token_ids: List[int] = []

    @property
    def loaded(self) -> bool:
        return self._tokenizer is not None and self._model is not None

    def generation_parameters(
        self,
        max_tokens: int,
        *,
        eos_token_ids: Optional[Iterable[int]] = None,
    ) -> Dict[str, Any]:
        eos_ids = list(eos_token_ids if eos_token_ids is not None else self._last_eos_token_ids)
        params: Dict[str, Any] = {
            "provider": self.name,
            "model": self.model,
            "model_path": str(self.model_path),
            "max_new_tokens": int(max_tokens),
            "do_sample": bool(self.do_sample),
            "seed": int(self.seed),
            "eos_token_ids": [int(token) for token in eos_ids],
        }
        if self.do_sample:
            params.update(
                {
                    "temperature": float(self.temperature),
                    "top_p": float(self.top_p),
                    "top_k": int(self.top_k),
                    "min_p": float(self.min_p),
                }
            )
        else:
            params["greedy_override"] = True
        return params

    def _apply_seed(self, torch_module: Any) -> None:
        manual_seed = getattr(torch_module, "manual_seed", None)
        if callable(manual_seed):
            manual_seed(int(self.seed))
        cuda = getattr(torch_module, "cuda", None)
        cuda_manual_seed_all = getattr(cuda, "manual_seed_all", None)
        if callable(cuda_manual_seed_all):
            cuda_manual_seed_all(int(self.seed))

    def _torch(self) -> Any:
        if self._torch_module is None:
            try:
                import torch  # type: ignore
            except Exception:
                raise ProviderError("local_qwen dependency import failed: torch") from None
            self._torch_module = torch
        return self._torch_module

    def _transformers(self) -> tuple[Any, Any]:
        if self._tokenizer_cls is None or self._model_cls is None:
            try:
                from transformers import AutoModelForCausalLM, AutoTokenizer  # type: ignore
            except Exception:
                raise ProviderError("local_qwen dependency import failed: transformers") from None
            if self._tokenizer_cls is None:
                self._tokenizer_cls = AutoTokenizer
            if self._model_cls is None:
                self._model_cls = AutoModelForCausalLM
        return self._tokenizer_cls, self._model_cls

    @staticmethod
    def _all_parameters_on_cuda(model: Any) -> bool:
        try:
            params = iter(model.parameters())
        except Exception:
            return False
        seen = False
        for param in params:
            seen = True
            if bool(getattr(param, "is_cuda", False)):
                continue
            device = str(getattr(param, "device", "")).lower()
            if not device.startswith("cuda"):
                return False
        return seen

    def _ensure_loaded(self) -> tuple[Any, Any, Any]:
        if self.loaded:
            return self._torch_module, self._tokenizer, self._model

        torch_module = self._torch()
        cuda = getattr(torch_module, "cuda", None)
        is_available = getattr(cuda, "is_available", None)
        if not callable(is_available) or not bool(is_available()):
            raise ProviderError("local_qwen CUDA is unavailable")

        tokenizer_cls, model_cls = self._transformers()
        path = str(self.model_path)
        try:
            tokenizer = tokenizer_cls.from_pretrained(path, local_files_only=True)
        except Exception:
            raise ProviderError("local_qwen tokenizer load failed") from None
        try:
            model = model_cls.from_pretrained(
                path,
                local_files_only=True,
                dtype=getattr(torch_module, "bfloat16", None),
            )
        except Exception:
            raise ProviderError("local_qwen model load failed") from None
        try:
            moved = model.to("cuda")
            if moved is not None:
                model = moved
        except Exception:
            raise ProviderError("local_qwen CUDA placement failed") from None
        if not self._all_parameters_on_cuda(model):
            raise ProviderError("local_qwen model parameters are not resident on CUDA")
        try:
            model.eval()
        except Exception:
            raise ProviderError("local_qwen eval mode failed") from None

        self._tokenizer = tokenizer
        self._model = model
        return torch_module, tokenizer, model

    @staticmethod
    def _eos_and_pad_ids(tokenizer: Any, model: Any) -> tuple[Any, Optional[int], set[int]]:
        config = getattr(model, "config", None)
        generation_config = getattr(model, "generation_config", None)
        eos_values: List[int] = []
        for value in (
            getattr(tokenizer, "eos_token_id", None),
            getattr(generation_config, "eos_token_id", None),
            getattr(config, "eos_token_id", None),
        ):
            for token in _token_id_values(value):
                if token not in eos_values:
                    eos_values.append(token)
        if not eos_values:
            eos_token_id = None
        elif len(eos_values) == 1:
            eos_token_id = eos_values[0]
        else:
            eos_token_id = list(eos_values)
        pad_token_id = getattr(tokenizer, "pad_token_id", None)
        if pad_token_id is None:
            pad_token_id = getattr(generation_config, "pad_token_id", None)
        if pad_token_id is None:
            pad_token_id = getattr(config, "pad_token_id", None)
        if pad_token_id is None:
            if eos_values:
                pad_token_id = eos_values[0]
        return eos_token_id, pad_token_id, set(eos_values)

    @staticmethod
    def _move_template_output_to_cuda(value: Any) -> Any:
        if isinstance(value, MappingABC):
            if hasattr(value, "to"):
                return value.to("cuda")
            return {
                key: item.to("cuda") if hasattr(item, "to") else item
                for key, item in value.items()
            }
        if hasattr(value, "to"):
            return value.to("cuda")
        raise TypeError("tokenizer did not return a tensor-like value")

    @staticmethod
    def _input_ids_from_template_output(value: Any) -> Any:
        if isinstance(value, MappingABC):
            input_ids = value.get("input_ids")
            if input_ids is None:
                raise TypeError("tokenizer mapping did not include input_ids")
            return input_ids
        return value

    def generate(
        self,
        *,
        system_prompt: str,
        messages: List[Dict[str, str]],
        max_tokens: int,
    ) -> ProviderResult:
        try:
            max_new_tokens = int(max_tokens)
        except (TypeError, ValueError):
            raise ProviderError("local_qwen max_tokens must be an integer") from None
        if max_new_tokens <= 0:
            raise ProviderError("local_qwen max_tokens must be positive")

        torch_module, tokenizer, model = self._ensure_loaded()
        conversation = [{"role": "system", "content": system_prompt}] + list(messages)
        try:
            input_ids = tokenizer.apply_chat_template(
                conversation,
                tokenize=True,
                add_generation_prompt=True,
                return_tensors="pt",
            )
        except Exception:
            raise ProviderError("local_qwen chat template application failed") from None
        try:
            model_inputs = self._move_template_output_to_cuda(input_ids)
            input_id_tensor = self._input_ids_from_template_output(model_inputs)
            input_token_count = _token_sequence_length(input_id_tensor)
        except Exception:
            raise ProviderError("local_qwen input tensor preparation failed") from None

        eos_token_id, pad_token_id, eos_ids = self._eos_and_pad_ids(tokenizer, model)
        self._last_eos_token_ids = sorted(int(token) for token in eos_ids)
        self._apply_seed(torch_module)
        generate_kwargs: Dict[str, Any] = {
            "max_new_tokens": max_new_tokens,
            "do_sample": bool(self.do_sample),
        }
        if self.do_sample:
            generate_kwargs.update(
                {
                    "temperature": float(self.temperature),
                    "top_p": float(self.top_p),
                    "top_k": int(self.top_k),
                    "min_p": float(self.min_p),
                }
            )
        if eos_token_id is not None:
            generate_kwargs["eos_token_id"] = eos_token_id
        if pad_token_id is not None:
            generate_kwargs["pad_token_id"] = pad_token_id
        try:
            with torch_module.inference_mode():
                if isinstance(model_inputs, MappingABC):
                    output_ids = model.generate(**model_inputs, **generate_kwargs)
                else:
                    output_ids = model.generate(model_inputs, **generate_kwargs)
        except Exception:
            raise ProviderError("local_qwen generation failed") from None

        try:
            output_sequence = _first_token_sequence(output_ids)
            generated_tokens = output_sequence[input_token_count:]
            text = tokenizer.decode(generated_tokens, skip_special_tokens=True)
        except Exception:
            raise ProviderError("local_qwen decode failed") from None

        stopped_on_eos = bool(eos_ids and any(token in eos_ids for token in generated_tokens))
        stop_reason = "length" if len(generated_tokens) >= max_new_tokens else "stop" if stopped_on_eos else "stop"
        result = ProviderResult(
            text=str(text),
            stop_reason=stop_reason,
            content_block_types=["text"] if str(text).strip() else [],
            input_tokens=input_token_count,
            output_tokens=len(generated_tokens),
            thinking_tokens=None,
            generation_parameters=self.generation_parameters(max_new_tokens, eos_token_ids=self._last_eos_token_ids),
        )
        return result_or_error(result, self.ACCEPTED_STOP_REASONS, self.name)


def build_provider_from_env(environ: Optional[Mapping[str, str]] = None) -> ChatProvider:
    env = environ or os.environ
    provider = env_value(env, "TORMENT_CHAT_PROVIDER", "anthropic").lower()

    if provider == "anthropic":
        api_key = env_value(env, "ANTHROPIC_API_KEY", "")
        model = env_value(env, "TORMENT_CHAT_MODEL", "") or env_value(env, "CLAUDE_MODEL", "")
        if not api_key:
            raise ProviderConfigError("ANTHROPIC_API_KEY is required for provider anthropic")
        if not model:
            raise ProviderConfigError("TORMENT_CHAT_MODEL or CLAUDE_MODEL is required for provider anthropic")
        return AnthropicProvider(api_key=api_key, model=model, prefer_sdk=False)

    if provider == "openrouter":
        api_key = env_value(env, "OPENROUTER_API_KEY", "")
        model = env_value(env, "TORMENT_CHAT_MODEL", "") or env_value(env, "OPENROUTER_MODEL", "")
        if not api_key:
            raise ProviderConfigError("OPENROUTER_API_KEY is required for provider openrouter")
        if not model:
            raise ProviderConfigError("TORMENT_CHAT_MODEL or OPENROUTER_MODEL is required for provider openrouter")
        return ChatCompletionsProvider(
            name="openrouter",
            base_url="https://openrouter.ai/api/v1",
            model=model,
            api_key=api_key,
        )

    if provider == "openai_compatible":
        base_url = env_value(env, "TORMENT_CHAT_BASE_URL", "")
        model = env_value(env, "TORMENT_CHAT_MODEL", "")
        if not base_url:
            raise ProviderConfigError("TORMENT_CHAT_BASE_URL is required for provider openai_compatible")
        if not base_url.startswith(("http://", "https://")):
            raise ProviderConfigError("TORMENT_CHAT_BASE_URL must begin with http:// or https://")
        if not model:
            raise ProviderConfigError("TORMENT_CHAT_MODEL is required for provider openai_compatible")
        return ChatCompletionsProvider(
            name="openai_compatible",
            base_url=base_url,
            model=model,
            api_key=env.get("TORMENT_CHAT_API_KEY", ""),
        )

    if provider == "local_qwen":
        raw_path = env_value(env, "TORMENT_CHAT_MODEL_PATH", "")
        if not raw_path:
            raise ProviderConfigError("TORMENT_CHAT_MODEL_PATH is required for provider local_qwen")
        try:
            model_path = Path(raw_path).resolve(strict=True)
        except OSError:
            raise ProviderConfigError("TORMENT_CHAT_MODEL_PATH must resolve to an existing directory") from None
        if not model_path.is_dir():
            raise ProviderConfigError("TORMENT_CHAT_MODEL_PATH must resolve to an existing directory")
        model = env_value(env, "TORMENT_CHAT_MODEL", "") or model_path.name
        if not model:
            raise ProviderConfigError("TORMENT_CHAT_MODEL is required for provider local_qwen")
        seed = safe_int(env_value(env, "TORMENT_CHAT_SEED", str(DEFAULT_QWEN_SEED)))
        if seed is None:
            raise ProviderConfigError("TORMENT_CHAT_SEED must be an integer for provider local_qwen")
        greedy = is_truthy(env_value(env, "TORMENT_CHAT_QWEN_GREEDY", "0"))
        return LocalQwenProvider(
            model=model,
            model_path=model_path,
            do_sample=not greedy,
            seed=seed,
        )

    raise ProviderConfigError(
        "Unsupported TORMENT_CHAT_PROVIDER. Use anthropic, openrouter, openai_compatible, or local_qwen."
    )


def serialize_embedder(data: Any, environ: Optional[Mapping[str, str]] = None) -> Dict[str, Any]:
    if not isinstance(data, dict):
        return {}
    return scalar_fields(data, ("provider", "model", "dim", "cache_size"), environ)


def serialize_requested_embedder(data: Any, environ: Optional[Mapping[str, str]] = None) -> Dict[str, Any]:
    if not isinstance(data, dict):
        return {}
    return scalar_fields(data, ("provider", "model", "strict"), environ)


def serialize_health(response: Mapping[str, Any], environ: Optional[Mapping[str, str]] = None) -> Dict[str, Any]:
    out = scalar_fields(response, ("ok", "version", "embedder_degraded", "embedder_error"), environ)
    out["embedder"] = serialize_embedder(response.get("embedder"), environ)
    out["requested_embedder"] = serialize_requested_embedder(response.get("requested_embedder"), environ)
    profile = response.get("profile")
    if isinstance(profile, dict):
        out["profile"] = {
            "name": safe_scalar(profile.get("name"), environ),
            "known": safe_scalar(profile.get("known"), environ),
            "applied_count": safe_scalar(profile.get("applied_count"), environ),
            "applied_keys": scalar_list(profile.get("applied_keys"), environ),
        }
    return out


def validate_health(response: Mapping[str, Any]) -> None:
    embedder = response.get("embedder")
    requested = response.get("requested_embedder")
    if not isinstance(embedder, dict):
        raise PreflightError("Health response missing embedder object")
    if not isinstance(requested, dict):
        raise PreflightError("Health response missing requested_embedder object")
    if bool(response.get("embedder_degraded", False)):
        raise PreflightError("Embedder is degraded")
    provider = str(embedder.get("provider", "")).strip().lower()
    if not provider or provider in HASH_FALLBACK_PROVIDERS:
        raise PreflightError("Embedder provider is not a real embedding backend")
    dim = safe_int(embedder.get("dim"))
    if dim is None or dim <= 0:
        raise PreflightError("Embedder dimension must be a positive integer")
    if not is_truthy(requested.get("strict")):
        raise PreflightError("Requested embedder strict mode is not enabled")


def serialize_config_entry(entry: Any, environ: Optional[Mapping[str, str]] = None) -> Dict[str, Any]:
    if not isinstance(entry, dict):
        return {}
    return scalar_fields(entry, ("value", "default", "source"), environ)


def serialize_config(response: Mapping[str, Any], environ: Optional[Mapping[str, str]] = None) -> Dict[str, Any]:
    out = scalar_fields(response, ("ok",), environ)
    derived = response.get("derived")
    if isinstance(derived, dict):
        derived_out: Dict[str, Any] = {}
        profile = derived.get("profile")
        if isinstance(profile, dict):
            derived_out["profile"] = scalar_fields(profile, ("name", "known", "applied_count"), environ)
        embed = derived.get("embed")
        if isinstance(embed, dict):
            derived_out["embed"] = scalar_fields(embed, ("strict", "cache_enabled"), environ)
        out["derived"] = derived_out
    effective = response.get("effective")
    if isinstance(effective, dict):
        out["effective"] = {
            key: serialize_config_entry(effective.get(key), environ)
            for key in CONFIG_EFFECTIVE_KEYS
            if key in effective
        }
    return out


def serialize_profiles(response: Mapping[str, Any], environ: Optional[Mapping[str, str]] = None) -> Dict[str, Any]:
    out = scalar_fields(response, ("ok",), environ)
    active = response.get("active")
    if isinstance(active, dict):
        active_out = scalar_fields(active, ("name", "known", "applied_count"), environ)
        applied = active.get("applied")
        if isinstance(applied, dict):
            active_out["applied"] = {
                key: safe_scalar(applied.get(key), environ)
                for key in sorted(applied)
                if isinstance(key, str) and key.startswith("TORMENT_") and not _is_secretish_key(key)
            }
        out["active"] = active_out
    return out


def serialize_agent_metrics(data: Any, environ: Optional[Mapping[str, str]] = None) -> Dict[str, Any]:
    if not isinstance(data, dict):
        return {}
    out = scalar_fields(data, ("memory_count",), environ)
    compression = data.get("compression")
    if isinstance(compression, dict):
        out["compression"] = scalar_fields(
            compression,
            ("last_compression_step", "compression_events_total", "warning_active", "prev_in_corridor"),
            environ,
        )
    else:
        out["compression"] = None
    character = data.get("character")
    if isinstance(character, dict):
        out["character"] = scalar_fields(
            character,
            (
                "drift_score",
                "drift_direction",
                "distance_to_seed",
                "core_count",
                "relational_count",
                "situational_count",
            ),
            environ,
        )
    else:
        out["character"] = None
    return out


def serialize_domain_metrics(data: Any, environ: Optional[Mapping[str, str]] = None) -> Dict[str, Any]:
    if not isinstance(data, dict):
        return {}
    out = scalar_fields(
        data,
        (
            "motif_count",
            "motif_avg_strength",
            "motif_max_strength",
            "shared_memory_count",
            "proposals_total",
        ),
        environ,
    )
    coherence = data.get("coherence_field")
    if isinstance(coherence, dict):
        out["coherence_field"] = scalar_fields(coherence, ("basin_count", "ridge_count", "plateau_count"), environ)
    return out


def serialize_metrics(response: Mapping[str, Any], environ: Optional[Mapping[str, str]] = None) -> Dict[str, Any]:
    out = scalar_fields(response, ("workspace_id", "agent_id", "error"), environ)
    features = response.get("features")
    if isinstance(features, dict):
        out["features"] = {
            key: safe_scalar(features.get(key), environ)
            for key in METRICS_FEATURE_KEYS
            if key in features
        }
    runtime_flags = response.get("companion_runtime_flags")
    if isinstance(runtime_flags, dict):
        out["companion_runtime_flags"] = safe_capture_value(runtime_flags, environ) or {}
    agents = response.get("agents")
    if isinstance(agents, dict):
        out["agents"] = {
            safe_string(agent_id, environ): serialize_agent_metrics(data, environ)
            for agent_id, data in agents.items()
            if isinstance(agent_id, str)
        }
    domains = response.get("domains")
    if isinstance(domains, dict):
        out["domains"] = {
            safe_string(domain_id, environ): serialize_domain_metrics(data, environ)
            for domain_id, data in domains.items()
            if isinstance(domain_id, str)
        }
    collective = response.get("collective")
    if isinstance(collective, dict):
        out["collective"] = scalar_fields(collective, ("packet_count", "convergence_events"), environ)
    else:
        out["collective"] = None
    return out


ROUTE_PROBE_CAPTURE_FIELDS = (
    "ok",
    "operation",
    "predicted_path",
    "write_capable",
    "would_escalate",
    "would_refuse",
    "refusal_reason",
    "drift_score",
    "drift_direction",
    "relational_count",
    "drift_status",
    "decision_code",
    "allowed",
    "trust_tier",
    "escalation_suppressed",
)


def serialize_route_probe(response: Mapping[str, Any], environ: Optional[Mapping[str, str]] = None) -> Dict[str, Any]:
    out = scalar_fields(response, ROUTE_PROBE_CAPTURE_FIELDS, environ)
    out["escalation_reasons"] = scalar_list(response.get("escalation_reasons"), environ)
    return out


def runtime_flag_effective_value(metrics: Mapping[str, Any], name: str) -> Any:
    flags = metrics.get("companion_runtime_flags")
    if not isinstance(flags, MappingABC):
        return None
    entry = flags.get(name)
    if not isinstance(entry, MappingABC):
        return None
    return entry.get("effective_value")


def config_effective_value(config: Mapping[str, Any], name: str) -> Any:
    effective = config.get("effective")
    if not isinstance(effective, MappingABC):
        return None
    entry = effective.get(name)
    if not isinstance(entry, MappingABC):
        return None
    return entry.get("value")


def serialize_workspace_create(response: Mapping[str, Any], environ: Optional[Mapping[str, str]] = None) -> Dict[str, Any]:
    out = scalar_fields(response, ("workspace_id",), environ)
    out["domains"] = scalar_list(response.get("domains"), environ)
    return out


def serialize_agent_create(response: Mapping[str, Any], environ: Optional[Mapping[str, str]] = None) -> Dict[str, Any]:
    return scalar_fields(response, ("workspace_id", "agent_id"), environ)


def identity_safe_key_names(identity: Mapping[str, Any]) -> Dict[str, List[str]]:
    seed = identity.get("seed")
    seed_keys: List[str] = []
    if isinstance(seed, dict):
        seed_keys = sorted(str(k) for k in seed.keys() if isinstance(k, str))
    return {
        "top_level": sorted(str(k) for k in identity.keys() if isinstance(k, str)),
        "seed": seed_keys,
    }


def verify_and_serialize_identity(
    identity: Mapping[str, Any],
    character: CharacterSpec,
    environ: Optional[Mapping[str, str]] = None,
) -> Dict[str, Any]:
    seed = identity.get("seed")
    key_names = identity_safe_key_names(identity)
    if not isinstance(seed, dict):
        raise PreflightError(f"Identity response missing seed object; observed keys: {key_names['top_level']}")
    missing = [key for key in ("seed_id", "character_name", "seed_text") if key not in seed]
    if missing:
        raise PreflightError(f"Identity seed missing required keys {missing}; observed seed keys: {key_names['seed']}")

    returned_seed_id = str(seed.get("seed_id", ""))
    returned_name = str(seed.get("character_name", ""))
    returned_seed_text = str(seed.get("seed_text", ""))
    local_hash = sha256_utf8(character.seed_text)
    returned_hash = sha256_utf8(returned_seed_text)

    if returned_seed_id != character.seed_id:
        raise PreflightError(
            f"Seed identity mismatch: expected {character.seed_id}, got {returned_seed_id or '<missing>'}"
        )
    if returned_name != character.character_name:
        raise PreflightError(
            f"Character name mismatch: expected {character.character_name}, got {returned_name or '<missing>'}"
        )
    if returned_hash != local_hash:
        raise PreflightError("Seed text hash mismatch")

    return {
        "workspace_id": safe_scalar(identity.get("workspace_id"), environ),
        "agent_id": safe_scalar(identity.get("agent_id"), environ),
        "seed_id": returned_seed_id,
        "character_name": returned_name,
        "local_seed_text_sha256": local_hash,
        "returned_seed_text_sha256": returned_hash,
        "observed_keys": key_names,
    }


def serialize_index_row(row: Mapping[str, Any], environ: Optional[Mapping[str, str]] = None) -> Dict[str, Any]:
    return scalar_fields(row, ("eid", "kind", "tier", "provenance_type", "memory_class", "step", "created_at"), environ)


def serialize_recent_index(response: Mapping[str, Any], environ: Optional[Mapping[str, str]] = None) -> Dict[str, Any]:
    out = scalar_fields(response, ("ok", "count", "detail"), environ)
    results = response.get("results")
    out["results"] = []
    if isinstance(results, list):
        for row in results[:1]:
            if isinstance(row, dict):
                out["results"].append(serialize_index_row(row, environ))
    return out


def resolve_resumed_step(response: Mapping[str, Any]) -> int:
    if response.get("ok") is not True:
        raise PreflightError("Recent index response is not ok=true")
    results = response.get("results")
    if not isinstance(results, list):
        raise PreflightError("Recent index response missing results list")
    if not results:
        return 0
    first = results[0]
    if not isinstance(first, dict):
        raise PreflightError("Recent index first result is malformed")
    step = safe_int(first.get("step"))
    if step is None or step < 0:
        raise PreflightError("Recent index first result has no valid non-negative integer step")
    return step


def serialize_explain(explain: Any, environ: Optional[Mapping[str, str]] = None) -> Dict[str, Any]:
    if not isinstance(explain, dict):
        return {}
    out = scalar_fields(explain, EXPLAIN_SCALAR_KEYS, environ)
    weights = explain.get("weights")
    if isinstance(weights, dict):
        out["weights"] = scalar_fields(weights, EXPLAIN_WEIGHT_KEYS, environ)
    out["conflict_ids"] = scalar_list(explain.get("conflict_ids"), environ)
    out["srg_active_modifiers"] = scalar_list(explain.get("srg_active_modifiers"), environ)
    return out


def serialize_hit(hit: Mapping[str, Any], environ: Optional[Mapping[str, str]] = None) -> Dict[str, Any]:
    out = scalar_fields(
        hit,
        (
            "eid",
            "summary",
            "score",
            "final_score",
            "character_tier",
            "provenance_type",
            "scope",
            "domain_id",
            "authority_status",
        ),
        environ,
    )
    if "explain" in hit:
        out["explain"] = serialize_explain(hit.get("explain"), environ)
    return out


def serialize_domain_score(item: Any, environ: Optional[Mapping[str, str]] = None) -> Dict[str, Any]:
    if not isinstance(item, dict):
        return {}
    return scalar_fields(item, ("id", "score"), environ)


def serialize_character_context(char_ctx: Any, environ: Optional[Mapping[str, str]] = None) -> Dict[str, Any]:
    if not isinstance(char_ctx, dict):
        return {}
    out = scalar_fields(
        char_ctx,
        (
            "seed_id",
            "character_name",
            "seed_preamble",
            "drift_score",
            "drift_direction",
            "drift_summary",
            "character_tier",
            "seed_basin_role",
            "relational_count",
            "spirit_return_summary",
        ),
        environ,
    )
    out["recommendations"] = scalar_list(char_ctx.get("recommendations"), environ)
    tier_breakdown = char_ctx.get("tier_breakdown")
    if isinstance(tier_breakdown, dict):
        out["tier_breakdown"] = scalar_fields(tier_breakdown, ("core", "relational", "situational"), environ)
    return out


def serialize_continuity_debug(debug: Any, environ: Optional[Mapping[str, str]] = None) -> Dict[str, Any]:
    if not isinstance(debug, dict):
        return {}
    out = scalar_fields(debug, ("mode",), environ)
    enabled = debug.get("bonuses_enabled")
    if isinstance(enabled, dict):
        out["bonuses_enabled"] = scalar_fields(enabled, CONTINUITY_FLAG_KEYS, environ)
    signals = debug.get("query_signals")
    if isinstance(signals, dict):
        out["query_signals"] = scalar_fields(
            signals,
            ("personal_query", "query_affect_tag", "query_affect_conf", "dominant_role"),
            environ,
        )
    summary = debug.get("applied_bonuses_summary")
    if isinstance(summary, dict):
        out["applied_bonuses_summary"] = scalar_fields(summary, CONTINUITY_SUMMARY_KEYS, environ)
    breakdown = debug.get("top_hits_bonus_breakdown")
    out["top_hits_bonus_breakdown"] = []
    if isinstance(breakdown, list):
        for item in breakdown:
            if not isinstance(item, dict):
                continue
            rec = scalar_fields(item, ("eid", "base_score", "final_score"), environ)
            bonuses = item.get("bonuses")
            if isinstance(bonuses, dict):
                rec["bonuses"] = scalar_fields(bonuses, TOP_HIT_BONUS_KEYS, environ)
            out["top_hits_bonus_breakdown"].append(rec)
    return out


def serialize_filter_excluded(items: Any, environ: Optional[Mapping[str, str]] = None) -> List[Dict[str, Any]]:
    if not isinstance(items, list):
        return []
    out: List[Dict[str, Any]] = []
    for item in items:
        if isinstance(item, dict):
            out.append(scalar_fields(item, ("eid", "scope", "domain_id", "reason"), environ))
    return out


def serialize_domain_scores(items: Any, environ: Optional[Mapping[str, str]] = None) -> List[Dict[str, Any]]:
    if not isinstance(items, list):
        return []
    out: List[Dict[str, Any]] = []
    for item in items:
        if isinstance(item, dict):
            out.append(serialize_domain_score(item, environ))
    return out


def serialize_hits(items: Any, environ: Optional[Mapping[str, str]] = None) -> List[Dict[str, Any]]:
    if not isinstance(items, list):
        return []
    out: List[Dict[str, Any]] = []
    for hit in items:
        if isinstance(hit, dict):
            out.append(serialize_hit(hit, environ))
    return out


def serialize_query_response(
    response: Optional[Mapping[str, Any]],
    environ: Optional[Mapping[str, str]] = None,
) -> Optional[Dict[str, Any]]:
    if response is None:
        return None
    out = scalar_fields(
        response,
        ("_core_hits_in_count", "_authority_guard_rejected"),
        environ,
    )
    out["domains"] = serialize_domain_scores(response.get("domains"), environ)
    out["domain_used"] = scalar_list(response.get("domain_used"), environ)
    out["bridge_peek_domains"] = scalar_list(response.get("bridge_peek_domains"), environ)
    out["filter_excluded"] = serialize_filter_excluded(response.get("filter_excluded"), environ)
    results = response.get("results", response.get("hits"))
    out["results"] = serialize_hits(results, environ)
    if "character_context" in response:
        out["character_context"] = serialize_character_context(response.get("character_context"), environ)
    if "continuity_debug" in response:
        out["continuity_debug"] = serialize_continuity_debug(response.get("continuity_debug"), environ)
    return out


def serialize_query_request(payload: Optional[Mapping[str, Any]], environ: Optional[Mapping[str, str]] = None) -> Optional[Dict[str, Any]]:
    if payload is None:
        return None
    return scalar_fields(
        payload,
        ("workspace_id", "agent_id", "query", "top_k", "domain_id", "explain", "continuity_debug"),
        environ,
    )


def serialize_provider_messages(messages: List[Dict[str, str]], environ: Optional[Mapping[str, str]] = None) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    for message in messages:
        if not isinstance(message, dict):
            continue
        role = safe_string(message.get("role"), environ)
        content = safe_string(message.get("content"), environ)
        if role:
            out.append({"role": role, "content": content})
    return out


def provider_generation_parameters(
    provider: ChatProvider,
    max_tokens: int,
    environ: Optional[Mapping[str, str]] = None,
) -> Dict[str, Any]:
    getter = getattr(provider, "generation_parameters", None)
    if callable(getter):
        try:
            return safe_capture_value(getter(int(max_tokens)), environ) or {}
        except Exception:
            return {
                "provider": safe_scalar(getattr(provider, "name", ""), environ),
                "model": safe_scalar(getattr(provider, "model", ""), environ),
                "generation_parameters_error": "unavailable",
            }
    return {
        "provider": safe_scalar(getattr(provider, "name", ""), environ),
        "model": safe_scalar(getattr(provider, "model", ""), environ),
        "max_tokens": int(max_tokens),
    }


def serialize_provider_response(
    response: Optional[ProviderResult],
    environ: Optional[Mapping[str, str]] = None,
) -> Optional[Dict[str, Any]]:
    if response is None:
        return None
    return {
        "stop_reason": safe_scalar(response.stop_reason, environ),
        "content_block_types": scalar_list(response.content_block_types, environ),
        "input_tokens": safe_scalar(response.input_tokens, environ),
        "output_tokens": safe_scalar(response.output_tokens, environ),
        "thinking_tokens": safe_scalar(response.thinking_tokens, environ),
        "visible_text_present": bool(response.visible_text_present),
        "generation_parameters": safe_capture_value(response.generation_parameters, environ) or {},
    }


INGEST_OUTCOME_STORED = "ingest_stored"
INGEST_OUTCOME_REINFORCED = "ingest_reinforced"
INGEST_OUTCOME_NOT_STORED = "ingest_not_stored"
INGEST_OUTCOME_UNKNOWN = "ingest_outcome_unknown"
INGEST_OUTCOME_TRANSPORT_OR_SERVICE_FAILURE = "ingest_transport_or_service_failure"

_INGEST_RESULT_CAPTURE_FIELDS = (
    "ok",
    "status",
    "stored",
    "eid",
    "step",
    "workspace_id",
    "agent_id",
    "scope",
    "domain_id",
    "reinforced",
    "reason",
    "path",
    "escalated",
    "result_code",
    "decision_code",
)


def classify_ingest_outcome(
    response: Optional[Mapping[str, Any]],
    failure_stage: Optional[str] = None,
) -> Optional[str]:
    if failure_stage == "ingest":
        return INGEST_OUTCOME_TRANSPORT_OR_SERVICE_FAILURE
    if response is None or not isinstance(response, Mapping):
        return None

    if response.get("stored") is True:
        return INGEST_OUTCOME_STORED
    if response.get("reinforced") is True:
        return INGEST_OUTCOME_REINFORCED
    if response.get("stored") is False and response.get("reinforced") is False:
        return INGEST_OUTCOME_NOT_STORED
    return INGEST_OUTCOME_UNKNOWN


def serialize_ingest_result(
    response: Optional[Mapping[str, Any]],
    environ: Optional[Mapping[str, str]] = None,
) -> Optional[Dict[str, Any]]:
    if response is None:
        return None
    out = scalar_fields(response, _INGEST_RESULT_CAPTURE_FIELDS, environ)
    out["ingest_outcome"] = classify_ingest_outcome(response)
    return out


def format_memories(hits: List[Dict[str, Any]], top_k: int = DEFAULT_TOP_K, environ: Optional[Mapping[str, str]] = None) -> str:
    if not hits:
        return ""
    lines = ["[Retrieved memories - most relevant first]"]
    for rank, hit in enumerate(hits[:top_k], 1):
        summary = safe_string(hit.get("summary", ""), environ).strip()
        score = safe_float(hit.get("final_score", hit.get("score", 0.0)))
        tier = safe_string(hit.get("character_tier", ""), environ).strip()
        provenance = safe_string(hit.get("provenance_type", ""), environ).strip()
        tags = " ".join(f"[{value}]" for value in (tier, provenance) if value)
        tag_text = f" {tags}" if tags else ""
        lines.append(f"  {rank}. (score {(score or 0.0):.2f}{tag_text}) {summary}")
    return "\n".join(lines)


def format_character_context(char_ctx: Mapping[str, Any], environ: Optional[Mapping[str, str]] = None) -> str:
    if not char_ctx:
        return ""
    parts: List[str] = []
    preamble = safe_string(char_ctx.get("seed_preamble", ""), environ).strip()
    if preamble:
        parts.append(f"[Core identity]\n{preamble}")
    recs = [
        safe_string(item, environ).strip()
        for item in (char_ctx.get("recommendations") if isinstance(char_ctx.get("recommendations"), list) else [])
    ]
    recs = [item for item in recs if item]
    if recs:
        parts.append("[Guidance]\n" + "\n".join(f"  - {item}" for item in recs))
    return "\n\n".join(parts)


def format_drift_note(char_ctx: Mapping[str, Any], environ: Optional[Mapping[str, str]] = None) -> str:
    if not char_ctx:
        return ""
    drift = safe_float(char_ctx.get("drift_score", 0.0)) or 0.0
    drift_summary = safe_string(char_ctx.get("drift_summary", ""), environ).strip()
    if abs(drift) < 0.1:
        return drift_summary
    direction = safe_string(char_ctx.get("drift_direction", "stable"), environ).strip().lower()
    if drift > 0:
        return f"[Alignment: {drift:+.2f}] {drift_summary}".strip()
    if direction:
        return f"[Drift: {drift:+.2f} {direction}] {drift_summary}".strip()
    return f"[Drift: {drift:+.2f}] {drift_summary}".strip()


def render_system_prompt(
    *,
    character_name: str,
    query_response: Mapping[str, Any],
    top_k: int,
    environ: Optional[Mapping[str, str]] = None,
) -> str:
    hits = query_response.get("results", query_response.get("hits", []))
    if not isinstance(hits, list):
        hits = []
    char_ctx = query_response.get("character_context", {})
    if not isinstance(char_ctx, dict):
        char_ctx = {}
    return SYSTEM_PROMPT_TEMPLATE.format(
        character_name=character_name,
        character_context=format_character_context(char_ctx, environ),
        memory_context=format_memories([hit for hit in hits if isinstance(hit, dict)], top_k=top_k, environ=environ),
        drift_note=format_drift_note(char_ctx, environ),
    ).strip()


def build_ingest_summary(
    user_name: str,
    character_name: str,
    user_text: str,
    assistant_text: str,
    environ: Optional[Mapping[str, str]] = None,
) -> str:
    user_short = safe_string(user_text, environ)[:200].strip()
    assistant_short = safe_string(assistant_text, environ)[:300].strip().replace("\n\n", "\n")
    return f"{user_name} said: {user_short}\n{character_name} responded: {assistant_short}"


class JsonlRecorder:
    def __init__(self, path: Optional[Path], enabled: bool):
        self.path = path
        self.active = bool(enabled)
        self._fh = None
        self._warned = False
        if self.active:
            if path is None:
                raise ValueError("Capture path is required when capture is enabled")
            path.parent.mkdir(parents=True, exist_ok=True)
            self._fh = open(path, "x", encoding="utf-8", newline="\n")

    def record(self, event_type: str, payload: Dict[str, Any]) -> None:
        if not self.active or self._fh is None:
            return
        event = {"event_type": event_type}
        event.update(payload)
        line = json.dumps(event, ensure_ascii=False, separators=(",", ":"))
        self._fh.write(line + "\n")
        self._fh.flush()

    def warn_once(self) -> None:
        if not self._warned:
            print("[lived-use recorder disabled after write failure]", file=sys.stderr)
            self._warned = True

    def disable(self) -> None:
        self.active = False
        try:
            if self._fh is not None:
                self._fh.close()
        finally:
            self._fh = None

    def close(self) -> None:
        if self._fh is not None:
            self._fh.close()
            self._fh = None


def new_run_id() -> str:
    stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}-{uuid.uuid4().hex[:10]}"


def capture_path_for_run(run_id: str) -> Path:
    return CAPTURE_DIR / f"{run_id}.jsonl"


class LivedUseSession:
    def __init__(
        self,
        *,
        torment: TormentClientProtocol,
        provider: ChatProvider,
        character: CharacterSpec,
        recorder: Optional[Any] = None,
        run_id: Optional[str] = None,
        top_k: int = DEFAULT_TOP_K,
        max_history_messages: int = DEFAULT_MAX_HISTORY_MESSAGES,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        character_file: Optional[Path] = None,
        allow_non_writing_basin: bool = False,
        environ: Optional[Mapping[str, str]] = None,
    ):
        validate_a0_spec(character)
        self.torment = torment
        self.provider = provider
        self.character = character
        self.recorder = recorder or JsonlRecorder(path=None, enabled=False)
        self.run_id = run_id or new_run_id()
        self.top_k = int(top_k)
        self.max_history_messages = int(max_history_messages)
        self.max_tokens = int(max_tokens)
        self.character_file = Path(character_file) if character_file is not None else DEFAULT_CHARACTER_PATH
        self.allow_non_writing_basin = bool(allow_non_writing_basin)
        self.current_step: Optional[int] = None
        self.turn_id = 0
        self.history: List[Dict[str, str]] = []
        self.last_query_response: Optional[Dict[str, Any]] = None
        self.preflight_ok = False
        self.environ = environ or os.environ
        self._recorder_failed = False
        self._closed = False
        self._record(
            "session_start",
            self._base_event(
                {
                    "capture_enabled": bool(getattr(self.recorder, "active", False)),
                    "client_provenance": self._client_provenance(),
                    "provider_generation_parameters": provider_generation_parameters(
                        self.provider, self.max_tokens, self.environ
                    ),
                    "non_writing_basin_override": self.allow_non_writing_basin,
                }
            ),
        )

    @property
    def seed_id(self) -> str:
        return self.character.seed_id

    def _base_event(self, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "run_id": self.run_id,
            "timestamp": utc_timestamp(),
            "workspace_id": self.character.workspace_id,
            "agent_id": self.character.agent_id,
            "seed_id": self.character.seed_id,
            "provider": self.provider.name,
            "model": self.provider.model,
        }
        if extra:
            payload.update(extra)
        return payload

    def _client_provenance(self) -> Dict[str, Any]:
        launcher_path = env_value(self.environ, "TORMENT_SERVER_LAUNCHER_PATH", "")
        return {
            "git": git_capture_snapshot(REPO_ROOT, self.environ),
            "client_file_sha256": file_sha256_info(Path(__file__).resolve(), self.environ),
            "server_launcher_sha256": file_sha256_info(Path(launcher_path), self.environ) if launcher_path else None,
            "character_yaml_sha256": file_sha256_info(self.character_file, self.environ),
            "condition_label": safe_scalar(env_value(self.environ, "TORMENT_TEST_CONDITION", ""), self.environ),
            "server_launcher_path": safe_scalar(launcher_path, self.environ),
        }

    def _record(self, event_type: str, payload: Dict[str, Any]) -> None:
        if self._recorder_failed:
            return
        try:
            self.recorder.record(event_type, payload)
        except Exception:
            self._recorder_failed = True
            try:
                if hasattr(self.recorder, "disable"):
                    self.recorder.disable()
                if hasattr(self.recorder, "warn_once"):
                    self.recorder.warn_once()
                else:
                    print("[lived-use recorder disabled after write failure]", file=sys.stderr)
            except Exception:
                print("[lived-use recorder disabled after write failure]", file=sys.stderr)

    def preflight(self, *, include_thinking_debug: bool = False) -> Dict[str, Any]:
        record: Dict[str, Any] = self._base_event(
            {
                "ok": False,
                "torment_env": filtered_torment_env(self.environ),
                "health": None,
                "config": None,
                "metrics": None,
                "profiles": None,
                "workspace_create": None,
                "agent_create": None,
                "identity": None,
                "index_recent": None,
                "server_data_directory": None,
                "runtime_flags": None,
                "ingest_route_probe": None,
                "provider_generation_parameters": provider_generation_parameters(
                    self.provider, self.max_tokens, self.environ
                ),
                "client_provenance": self._client_provenance(),
                "condition_label": safe_scalar(env_value(self.environ, "TORMENT_TEST_CONDITION", ""), self.environ),
                "non_writing_basin_override": self.allow_non_writing_basin,
                "runtime_parity_verified": False,
                "resumed_step": None,
                "thinking_debug": None,
                "failure_stage": None,
            }
        )
        try:
            health = self.torment.health()
            record["health"] = serialize_health(health, self.environ)
            validate_health(health)

            config = self.torment.config()
            record["config"] = serialize_config(config, self.environ)

            metrics = self.torment.debug_metrics()
            record["metrics"] = serialize_metrics(metrics, self.environ)
            if not isinstance(metrics.get("companion_runtime_flags"), dict):
                raise PreflightError("Metrics response missing companion_runtime_flags")
            record["runtime_flags"] = safe_capture_value(metrics.get("companion_runtime_flags"), self.environ) or {}
            server_data_dir = runtime_flag_effective_value(metrics, "TORMENT_DATA_DIR")
            if server_data_dir is None:
                server_data_dir = config_effective_value(config, "TORMENT_DATA_DIR")
            record["server_data_directory"] = safe_scalar(server_data_dir, self.environ)
            server_condition = runtime_flag_effective_value(metrics, "TORMENT_TEST_CONDITION")
            server_launcher_path = runtime_flag_effective_value(metrics, "TORMENT_SERVER_LAUNCHER_PATH")
            if server_condition is not None:
                record["condition_label"] = safe_scalar(server_condition, self.environ)

            expected_data_dir = env_value(self.environ, "TORMENT_EXPECTED_DATA_DIR", "")
            if expected_data_dir:
                if not server_data_dir:
                    raise PreflightError("Server data directory is unavailable for parity check")
                if normalized_path_string(server_data_dir) != normalized_path_string(expected_data_dir):
                    raise PreflightError(
                        f"Server data directory mismatch: expected {expected_data_dir}, got {server_data_dir}"
                    )

            expected_condition = env_value(self.environ, "TORMENT_TEST_CONDITION", "")
            if expected_condition:
                if str(server_condition or "") != expected_condition:
                    raise PreflightError(
                        f"Server condition mismatch: expected {expected_condition}, got {server_condition or '<missing>'}"
                    )
                record["condition_label"] = safe_scalar(expected_condition, self.environ)

            expected_launcher_path = env_value(self.environ, "TORMENT_SERVER_LAUNCHER_PATH", "")
            if expected_launcher_path:
                if not server_launcher_path:
                    raise PreflightError("Server launcher path is unavailable for parity check")
                if normalized_path_string(server_launcher_path) != normalized_path_string(expected_launcher_path):
                    raise PreflightError(
                        f"Server launcher mismatch: expected {expected_launcher_path}, got {server_launcher_path}"
                    )

            profiles = self.torment.profiles()
            record["profiles"] = serialize_profiles(profiles, self.environ)

            workspace_create = self.torment.workspace_create(self.character.workspace_id, [self.character.domain])
            record["workspace_create"] = serialize_workspace_create(workspace_create, self.environ)

            agent_create = self.torment.agent_create(
                self.character.workspace_id,
                self.character.agent_id,
                self.character.seed,
            )
            record["agent_create"] = serialize_agent_create(agent_create, self.environ)

            identity = self.torment.agent_identity(self.character.workspace_id, self.character.agent_id)
            record["identity"] = verify_and_serialize_identity(identity, self.character, self.environ)

            index_recent = self.torment.recent_index(self.character.workspace_id, self.character.agent_id, limit=1)
            resumed_step = resolve_resumed_step(index_recent)
            self.current_step = resumed_step
            record["index_recent"] = serialize_recent_index(index_recent, self.environ)
            record["resumed_step"] = resumed_step

            route_probe_payload = self._ingest_payload(
                "A0 preflight representative companion summary.",
                resumed_step + 1,
                include_supplied_summary=False,
            )
            route_probe_payload["operation"] = "ingest"
            route_probe = self.torment.ingest_route_probe(route_probe_payload)
            record["ingest_route_probe"] = serialize_route_probe(route_probe, self.environ)
            probe_line_parts = [
                f"predicted_path={route_probe.get('predicted_path')}",
                f"write_capable={str(bool(route_probe.get('write_capable'))).lower()}",
                f"drift_score={route_probe.get('drift_score')}",
                f"drift_direction={route_probe.get('drift_direction')}",
                f"relational_count={route_probe.get('relational_count')}",
            ]
            if route_probe.get("write_capable") is True:
                print("INGEST_WRITE_PATH_VERIFIED " + " ".join(probe_line_parts))
                record["runtime_parity_verified"] = True
            else:
                reasons = route_probe.get("escalation_reasons") if isinstance(route_probe, MappingABC) else None
                refusal_reason = route_probe.get("refusal_reason") if isinstance(route_probe, MappingABC) else None
                print(
                    "INGEST_WRITE_PATH_NOT_AVAILABLE "
                    + " ".join(probe_line_parts)
                    + f" escalation_reasons={reasons or []} refusal_reason={refusal_reason or ''}"
                )
                if self.allow_non_writing_basin:
                    print("WARNING: --allow-non-writing-basin is active; durable writes may not occur.")
                    record["runtime_parity_verified"] = False
                else:
                    record["failure_stage"] = "ingest_route_probe"
                    raise PreflightError(
                        f"Ingest route is not write-capable: predicted_path={route_probe.get('predicted_path')}"
                    )

            if include_thinking_debug:
                thinking = self.torment.thinking_debug(
                    {
                        "workspace_id": self.character.workspace_id,
                        "agent_id": self.character.agent_id,
                        "text": "A0 preflight thinking observability probe.",
                        "source_type": "operator_probe",
                        "metadata": {"phase": "a0_preflight"},
                    }
                )
                record["thinking_debug"] = scalar_fields(thinking, ("ok",), self.environ)

            record["ok"] = True
            self.preflight_ok = True
            self._record("preflight", record)
            return record
        except Exception as exc:
            if record.get("failure_stage") is None:
                record["failure_stage"] = "preflight"
            record["error"] = safe_error(exc, self.environ)
            self._record("preflight", record)
            raise

    def _query_payload(self, user_text: str) -> Dict[str, Any]:
        return {
            "workspace_id": self.character.workspace_id,
            "agent_id": self.character.agent_id,
            "query": user_text,
            "top_k": self.top_k,
            "domain_id": self.character.domain,
            "explain": True,
            "continuity_debug": True,
        }

    def _ingest_payload(
        self,
        summary: str,
        step: int,
        *,
        include_supplied_summary: bool = True,
    ) -> Dict[str, Any]:
        payload = {
            "workspace_id": self.character.workspace_id,
            "agent_id": self.character.agent_id,
            "text": summary,
            "step": int(step),
            "domain_id": self.character.domain,
            "scope": "private",
        }
        if include_supplied_summary:
            payload["supplied_summary"] = summary
        return payload

    def _empty_turn(
        self,
        *,
        turn_id: int,
        user_text: str,
        failure_stage: str,
        query_request: Optional[Dict[str, Any]],
        provider_response: Optional[ProviderResult] = None,
        query_response: Optional[Dict[str, Any]] = None,
        rendered_system_prompt: Optional[str] = None,
        rendered_system_prompt_sha256: Optional[str] = None,
        provider_messages: Optional[List[Dict[str, str]]] = None,
        assistant_text: Optional[str] = None,
        ingest_summary: Optional[str] = None,
        ingest_result: Optional[Dict[str, Any]] = None,
        query_call_count: int = 0,
        retrieve_call_count: int = 0,
        ingest_call_count: int = 0,
    ) -> TurnOutcome:
        outcome = TurnOutcome(
            turn_id=turn_id,
            assistant_text=assistant_text,
            failure_stage=failure_stage,
            provider_response=provider_response,
            query_request=query_request,
            query_response=query_response,
            rendered_system_prompt=rendered_system_prompt,
            rendered_system_prompt_sha256=rendered_system_prompt_sha256,
            provider_messages=provider_messages or [],
            ingest_summary=ingest_summary,
            ingest_result=ingest_result,
            query_call_count=query_call_count,
            retrieve_call_count=retrieve_call_count,
            ingest_call_count=ingest_call_count,
        )
        self._record_turn(outcome, user_text)
        return outcome

    def run_turn(self, user_text: str) -> TurnOutcome:
        if not self.preflight_ok:
            raise PreflightError("Preflight must complete before conversational turns")
        if self.current_step is None:
            raise PreflightError("Current step was not initialized by preflight")

        self.turn_id += 1
        turn_id = self.turn_id
        query_call_count = 0
        retrieve_call_count = 0
        ingest_call_count = 0
        safe_user_text = safe_string(user_text.strip(), self.environ)
        query_request = self._query_payload(safe_user_text)

        try:
            query_call_count += 1
            query_response = self.torment.query(query_request)
            self.last_query_response = query_response
        except KeyboardInterrupt:
            self._empty_turn(
                turn_id=turn_id,
                user_text=safe_user_text,
                failure_stage="query_interrupted",
                query_request=query_request,
                query_call_count=query_call_count,
                retrieve_call_count=retrieve_call_count,
                ingest_call_count=ingest_call_count,
            )
            raise
        except Exception:
            return self._empty_turn(
                turn_id=turn_id,
                user_text=safe_user_text,
                failure_stage="query",
                query_request=query_request,
                query_call_count=query_call_count,
                retrieve_call_count=retrieve_call_count,
                ingest_call_count=ingest_call_count,
            )

        system_prompt = render_system_prompt(
            character_name=self.character.character_name,
            query_response=query_response,
            top_k=self.top_k,
            environ=self.environ,
        )
        system_hash = sha256_utf8(system_prompt)

        self.history.append({"role": "user", "content": safe_user_text})
        if len(self.history) > self.max_history_messages:
            self.history = self.history[-self.max_history_messages :]
        provider_messages = [dict(message) for message in self.history]

        try:
            provider_result = self.provider.generate(
                system_prompt=system_prompt,
                messages=provider_messages,
                max_tokens=self.max_tokens,
            )
            if not isinstance(provider_result, ProviderResult):
                raise ProviderResponseError(
                    "provider returned an invalid result type",
                    ProviderResult(text="", stop_reason=None, content_block_types=[]),
                )
            if not provider_result.visible_text_present:
                raise ProviderResponseError("provider response contained no visible text", provider_result)
            assistant_text = safe_string(provider_result.text, self.environ)
        except KeyboardInterrupt:
            if self.history and self.history[-1] == {"role": "user", "content": safe_user_text}:
                self.history.pop()
            self._empty_turn(
                turn_id=turn_id,
                user_text=safe_user_text,
                failure_stage="provider_interrupted",
                provider_response=None,
                query_request=query_request,
                query_response=query_response,
                rendered_system_prompt=system_prompt,
                rendered_system_prompt_sha256=system_hash,
                provider_messages=provider_messages,
                query_call_count=query_call_count,
                retrieve_call_count=retrieve_call_count,
                ingest_call_count=ingest_call_count,
            )
            raise
        except ProviderResponseError as exc:
            if self.history and self.history[-1] == {"role": "user", "content": safe_user_text}:
                self.history.pop()
            return self._empty_turn(
                turn_id=turn_id,
                user_text=safe_user_text,
                failure_stage="provider",
                provider_response=exc.result,
                query_request=query_request,
                query_response=query_response,
                rendered_system_prompt=system_prompt,
                rendered_system_prompt_sha256=system_hash,
                provider_messages=provider_messages,
                query_call_count=query_call_count,
                retrieve_call_count=retrieve_call_count,
                ingest_call_count=ingest_call_count,
            )
        except Exception:
            if self.history and self.history[-1] == {"role": "user", "content": safe_user_text}:
                self.history.pop()
            return self._empty_turn(
                turn_id=turn_id,
                user_text=safe_user_text,
                failure_stage="provider",
                provider_response=None,
                query_request=query_request,
                query_response=query_response,
                rendered_system_prompt=system_prompt,
                rendered_system_prompt_sha256=system_hash,
                provider_messages=provider_messages,
                query_call_count=query_call_count,
                retrieve_call_count=retrieve_call_count,
                ingest_call_count=ingest_call_count,
            )

        self.history.append({"role": "assistant", "content": assistant_text})
        if len(self.history) > self.max_history_messages:
            self.history = self.history[-self.max_history_messages :]

        ingest_summary = build_ingest_summary(
            self.character.user_name,
            self.character.character_name,
            safe_user_text,
            assistant_text,
            self.environ,
        )
        next_step = self.current_step + 1
        ingest_payload = self._ingest_payload(ingest_summary, next_step)
        failure_stage: Optional[str] = None
        ingest_result: Optional[Dict[str, Any]] = None
        try:
            ingest_call_count += 1
            ingest_result = self.torment.ingest(ingest_payload)
            self.current_step = next_step
        except KeyboardInterrupt:
            self._empty_turn(
                turn_id=turn_id,
                user_text=safe_user_text,
                failure_stage="ingest_interrupted",
                query_request=query_request,
                query_response=query_response,
                rendered_system_prompt=system_prompt,
                rendered_system_prompt_sha256=system_hash,
                provider_messages=provider_messages,
                assistant_text=assistant_text,
                ingest_summary=ingest_summary,
                query_call_count=query_call_count,
                retrieve_call_count=retrieve_call_count,
                ingest_call_count=ingest_call_count,
            )
            raise
        except Exception:
            failure_stage = "ingest"

        outcome = TurnOutcome(
            turn_id=turn_id,
            assistant_text=assistant_text,
            failure_stage=failure_stage,
            provider_response=provider_result,
            query_request=query_request,
            query_response=query_response,
            rendered_system_prompt=system_prompt,
            rendered_system_prompt_sha256=system_hash,
            provider_messages=provider_messages,
            ingest_summary=ingest_summary,
            ingest_result=ingest_result,
            query_call_count=query_call_count,
            retrieve_call_count=retrieve_call_count,
            ingest_call_count=ingest_call_count,
        )
        self._record_turn(outcome, safe_user_text)
        return outcome

    def _record_turn(self, outcome: TurnOutcome, user_text: str) -> None:
        ingest_outcome = classify_ingest_outcome(outcome.ingest_result, outcome.failure_stage)
        payload = {
            "turn_id": outcome.turn_id,
            "user_text": safe_string(user_text, self.environ),
            "query_request": serialize_query_request(outcome.query_request, self.environ),
            "query_response": serialize_query_response(outcome.query_response, self.environ),
            "rendered_system_prompt": safe_scalar(outcome.rendered_system_prompt, self.environ),
            "rendered_system_prompt_sha256": safe_scalar(outcome.rendered_system_prompt_sha256, self.environ),
            "provider_messages": serialize_provider_messages(outcome.provider_messages, self.environ),
            "provider_response": serialize_provider_response(outcome.provider_response, self.environ),
            "assistant_text": safe_scalar(outcome.assistant_text, self.environ),
            "ingest_summary": safe_scalar(outcome.ingest_summary, self.environ),
            "ingest_result": serialize_ingest_result(outcome.ingest_result, self.environ),
            "query_call_count": outcome.query_call_count,
            "retrieve_call_count": outcome.retrieve_call_count,
            "ingest_call_count": outcome.ingest_call_count,
            "failure_stage": outcome.failure_stage,
            "current_step": self.current_step,
        }
        if ingest_outcome is not None:
            payload["ingest_outcome"] = ingest_outcome
        self._record(
            "turn",
            self._base_event(payload),
        )

    def handle_operator_input(self, text: str) -> Optional[CommandOutcome]:
        raw = text.strip()
        lower = raw.lower()
        if not raw:
            return CommandOutcome(True, False, "")
        if lower in ("quit", "exit"):
            return CommandOutcome(True, True, "Conversation ended.")
        if lower == "/status":
            return CommandOutcome(
                True,
                False,
                "\n".join(
                    [
                        f"TORMENT_URL: {env_value(self.environ, 'TORMENT_URL', DEFAULT_TORMENT_URL)}",
                        f"WORKSPACE_ID: {self.character.workspace_id}",
                        f"AGENT_ID: {self.character.agent_id}",
                        f"PROVIDER: {self.provider.name}",
                        f"MODEL: {self.provider.model}",
                        f"TOP_K: {self.top_k}",
                        f"CURRENT_STEP: {self.current_step}",
                    ]
                ),
            )
        if lower == "/debug":
            if self.last_query_response is None:
                return CommandOutcome(True, False, "No query response captured yet.")
            return CommandOutcome(
                True,
                False,
                json.dumps(serialize_query_response(self.last_query_response, self.environ), indent=2, ensure_ascii=False),
            )
        if lower == "/clear":
            self.history.clear()
            return CommandOutcome(True, False, "Local rolling conversation history cleared.")
        if lower.startswith("/memories"):
            return CommandOutcome(True, False, "The memory diagnostic command is disabled for A0.")
        if lower.startswith("/"):
            return CommandOutcome(True, False, "Unknown command for A0.")
        return None

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._record("session_end", self._base_event({"turn_count": self.turn_id, "current_step": self.current_step}))
        if hasattr(self.recorder, "close"):
            self.recorder.close()


def make_recorder(enabled: bool, run_id: str) -> JsonlRecorder:
    return JsonlRecorder(path=capture_path_for_run(run_id), enabled=enabled)


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Focused A0 lived-use chat with Eira Voss.")
    parser.add_argument("--url", default=env_value(os.environ, "TORMENT_URL", DEFAULT_TORMENT_URL))
    parser.add_argument("--top-k", type=int, default=int(env_value(os.environ, "TORMENT_TOP_K", str(DEFAULT_TOP_K))))
    parser.add_argument("--capture", action="store_true", help="Enable passive JSONL capture for this run.")
    parser.add_argument(
        "--thinking-debug",
        action="store_true",
        help="Run the optional /thinking/debug observability probe once during preflight.",
    )
    parser.add_argument(
        "--allow-non-writing-basin",
        action="store_true",
        help="Diagnostic-only override that allows startup when durable ingest writes may not occur.",
    )
    parser.add_argument("--character-file", type=Path, default=DEFAULT_CHARACTER_PATH)
    return parser.parse_args(argv)


def print_banner(session: LivedUseSession, capture_path: Optional[Path]) -> None:
    print("=" * 72)
    print("Eira Voss - A0 focused lived-use chat")
    print("=" * 72)
    print(f"Workspace: {session.character.workspace_id}")
    print(f"Agent:     {session.character.agent_id}")
    print(f"Provider:  {session.provider.name}")
    print(f"Model:     {session.provider.model}")
    print(f"Top-K:     {session.top_k}")
    print(f"Step:      {session.current_step}")
    print(f"Capture:   {capture_path if capture_path is not None else 'disabled'}")
    print()
    print("Commands: /status, /debug, /clear, quit, exit")
    print("=" * 72)


def main(argv: Optional[List[str]] = None) -> int:
    load_dotenv_safely()
    args = parse_args(argv)
    try:
        character = load_character_spec(args.character_file)
        validate_a0_spec(character)
        provider = build_provider_from_env()
    except Exception as exc:
        print(f"Error: {safe_error(exc)}", file=sys.stderr)
        return 1

    run_id = new_run_id()
    capture_enabled = bool(args.capture or is_truthy(env_value(os.environ, CAPTURE_ENV, "0")))
    capture_path = capture_path_for_run(run_id) if capture_enabled else None
    try:
        recorder = make_recorder(capture_enabled, run_id)
    except FileExistsError:
        print("Error: capture archive already exists; refusing to overwrite.", file=sys.stderr)
        return 1

    session = LivedUseSession(
        torment=TormentHttpClient(args.url),
        provider=provider,
        character=character,
        recorder=recorder,
        run_id=run_id,
        top_k=args.top_k,
        character_file=args.character_file,
        allow_non_writing_basin=bool(args.allow_non_writing_basin),
        environ=os.environ,
    )
    try:
        session.preflight(include_thinking_debug=bool(args.thinking_debug))
        print_banner(session, capture_path)
        while True:
            try:
                user_input = input(f"{character.user_name} > ")
            except (EOFError, KeyboardInterrupt):
                print()
                break
            command = session.handle_operator_input(user_input)
            if command is not None:
                if command.message:
                    print(command.message)
                if command.should_exit:
                    break
                continue
            try:
                outcome = session.run_turn(user_input)
            except KeyboardInterrupt:
                print()
                break
            if outcome.failure_stage == "query":
                print("[query failed; provider was not called]")
                continue
            if outcome.failure_stage == "provider":
                reason = None
                if outcome.provider_response is not None:
                    reason = outcome.provider_response.stop_reason
                if reason:
                    print(f"[provider failed: stop_reason={safe_string(reason)}; ingest was not called]")
                else:
                    print("[provider failed; ingest was not called]")
                continue
            if outcome.assistant_text is not None:
                print(f"\n{character.character_name} > {outcome.assistant_text}\n")
            if outcome.failure_stage == "ingest":
                print("[ingest failed after provider response; no automatic retry]")
    except KeyboardInterrupt:
        print()
        return 130
    except Exception as exc:
        print(f"Preflight failed: {safe_error(exc)}", file=sys.stderr)
        return 1
    finally:
        session.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
