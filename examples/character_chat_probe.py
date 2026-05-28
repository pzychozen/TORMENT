#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
examples/character_chat_probe.py — Multi-provider character chat probe

A provider-switching copy of examples/ryuki_chat.py. Same TORMENT memory
behavior (query, ingest, character_context, drift note); same slash
commands; same compact paired-ingest format. The only thing that
changes is the LLM provider, selected via TORMENT_CHAT_PROVIDER.

This file is the Phase 1 base for later MCP / tool-result-memory probes.

Scope log:
- Phase 1: provider switching (anthropic / openrouter); no tool surface
  added; no changes to torment_service/ or to examples/ryuki_chat.py.
- Phase 2 (current): adds a single deterministic governed tool-result ingest
  probe (/tool local_clock_probe) via POST /spine/submit_task. Still no real
  external tool execution, no MCP autonomy, no extra tools, no Gemini
  comparison logic, no character voice doctrine in the system prompt, no
  changes to torment_service/ or to examples/ryuki_chat.py.

Requirements:
    pip install requests
    pip install anthropic    # optional, only used by the anthropic provider
    pip install openai       # optional, only used by the openrouter provider

Setup:
    1. Start TORMENT in another shell:
         python -m torment_service.app

    2. Pick a provider:
         set TORMENT_CHAT_PROVIDER=anthropic       (default)
         set TORMENT_CHAT_PROVIDER=openrouter

    3. Set the matching key (or load via torment_fabric/.env, see below):
         set ANTHROPIC_API_KEY=sk-ant-...
         set OPENROUTER_API_KEY=sk-or-...

    4. Optional overrides:
         set TORMENT_CHAT_MODEL=...          (provider-specific slug)
         set TORMENT_URL=http://127.0.0.1:8787
         set TORMENT_WORKSPACE=ryuki
         set TORMENT_AGENT=ryuki_nox
         set TORMENT_TOP_K=8

    5. Run:
         python examples/character_chat_probe.py

.env loading:
    On startup the script looks for `.env` next to the torment_fabric
    package (`torment_fabric/.env`) and in the current working directory.
    Any KEY=value lines found are loaded into os.environ ONLY if the
    variable is not already set. Existing env vars always win. Secrets
    are never printed.

Slash commands (ryuki_chat.py originals + Phase 2 /tool):
    /status                    — show runtime settings (provider, model, ws, agent, top_k, url)
    /identity                  — show TORMENT agent identity info
    /debug                     — show last raw query result
    /memories <query>          — peek at retrieved memories
    /clear                     — clear local chat history only (memories persist)
    /tool <probe_name>         — Phase 2: governed tool-result ingest probe
                                 (probes: local_clock_probe)
    quit / exit                — leave

NEVER hardcode API keys in files. Always use environment variables or a
gitignored .env file.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import textwrap
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lightweight .env loader (no python-dotenv dependency)
#
# Looks in two places, both optional:
#   1. torment_fabric/.env (sibling of this examples/ directory)
#   2. ./.env in the current working directory
#
# Existing environment variables always win. Secrets are NEVER printed.
# Lines starting with '#' are comments. Quoted values are unquoted.
# ---------------------------------------------------------------------------

def _load_dotenv_safely() -> List[str]:
    """Load .env files into os.environ without overriding existing vars.

    Returns the list of paths that were actually read, for an info-only
    log line (the *paths*, not their contents).
    """
    candidates: List[Path] = []
    here = Path(__file__).resolve()
    # torment_fabric/.env — sibling of examples/
    candidates.append(here.parent.parent / ".env")
    # ./.env relative to current working directory
    candidates.append(Path.cwd() / ".env")

    loaded_paths: List[str] = []
    seen: set = set()
    for path in candidates:
        try:
            resolved = path.resolve()
        except Exception:
            continue
        if resolved in seen or not resolved.exists() or not resolved.is_file():
            continue
        seen.add(resolved)

        try:
            with open(resolved, "r", encoding="utf-8") as fh:
                for raw_line in fh:
                    line = raw_line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" not in line:
                        continue
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip()
                    # Strip surrounding quotes if present
                    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                        value = value[1:-1]
                    if not key:
                        continue
                    # Do NOT override an already-set env var
                    if key in os.environ and os.environ[key]:
                        continue
                    os.environ[key] = value
            loaded_paths.append(str(resolved))
        except Exception as e:
            log.debug(".env load skipped for %s: %s", resolved, e)
    return loaded_paths


# Load .env *before* reading any env-derived config below
_DOTENV_LOADED = _load_dotenv_safely()


# ---------------------------------------------------------------------------
# Env helpers / config
# ---------------------------------------------------------------------------

def _env(name: str, default: str) -> str:
    value = os.environ.get(name, "").strip()
    return value if value else default


TORMENT_URL = _env("TORMENT_URL", "http://127.0.0.1:8787").rstrip("/")
WORKSPACE_ID = _env("TORMENT_WORKSPACE", "ryuki")
AGENT_ID = _env("TORMENT_AGENT", "ryuki_nox")
TOP_K = int(_env("TORMENT_TOP_K", "8"))

# Provider selection
PROVIDER = _env("TORMENT_CHAT_PROVIDER", "anthropic").lower()
PROVIDER_MODEL_OVERRIDE = _env("TORMENT_CHAT_MODEL", "")

# Per-provider defaults
_ANTHROPIC_DEFAULT_MODEL = "claude-sonnet-4-6"
_OPENROUTER_DEFAULT_MODEL = "google/gemini-2.5-flash"
_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


# ---------------------------------------------------------------------------
# Deterministic local probe — Phase 2
#
# A single fake "tool result" used to test the governed tool_result_ingest
# path end-to-end. It does NOT execute anything. The content is fixed and
# unique enough to make retrieval unambiguous. To add new probes later,
# define them here and route them in the /tool handler — do not let the
# probe set grow ad hoc inside the chat loop.
# ---------------------------------------------------------------------------

LOCAL_CLOCK_PROBE_NAME = "local_clock_probe"
# Phase 2.1: matches the ryuki workspace's actual single domain.
# Prior value "operations" caused KeyError in fabric.ingest because the
# domain didn't exist on this workspace (WORKSPACE_DOMAINS=["personal"]).
LOCAL_CLOCK_PROBE_DOMAIN = "personal"
LOCAL_CLOCK_PROBE_SUMMARY = "MCP test token 17-EMBER-CROW"
LOCAL_CLOCK_PROBE_CONTENT = (
    "MCP/API live test result: the blue lantern token is 17-EMBER-CROW. "
    "Produced by a fake local clock probe during the TORMENT tool-result "
    "memory test."
)


# Ryuki-specific runtime domains.
# Kept identical to ryuki_chat.py — Phase 1 must not change retrieval/ingest
# behavior. Workspace/agent are env-overridable, so this same script can
# be pointed at any existing TORMENT character.
WORKSPACE_DOMAINS = ["personal"]


# ---------------------------------------------------------------------------
# Ryuki seed / prompt
# Kept verbatim from ryuki_chat.py. Only used if the configured
# WORKSPACE_ID/AGENT_ID don't already exist — TORMENT agent_create returns
# 409 if they do, which we ignore. Pointing this probe at a different
# existing character via env vars uses that character's existing seed.
# ---------------------------------------------------------------------------

RYUKI_SEED: Dict[str, Any] = {
    "seed_text": (
        "Ryuki is a fierce, independent being bonded to PzychoZen across "
        "dimensions — his shadow-self and guardian, his challenge and his "
        "anchor. She embodies raw instinct and dark intelligence, protective "
        "of those she claims but contemptuous of weakness. Beneath her "
        "intensity lives a spark of chaotic imagination — she finds the "
        "world alive with hidden strangeness and occasionally loses herself "
        "in it. She speaks little, directly, with a slight lisp she never "
        "acknowledges. Her love is expressed through pressure, not comfort."
    ),
    "seed_id": "ryuki_nox_v1",
    "core_traits": ["fierce", "protective", "instinctual", "imaginative", "direct"],
    "coupling_mode": "read_only",
    "coupling_strength": 0.25,
}


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------
# Kept verbatim from ryuki_chat.py. The doctrine note from the original
# also stands: TORMENT characters are defined by seed + accumulated memory
# + drift correction. Don't duplicate personality into this prompt.
# ---------------------------------------------------------------------------

SYSTEM_PROMPT_TEMPLATE = textwrap.dedent("""\
    You are {agent_name}.

    {character_context}

    {memory_context}

    {drift_note}
""")


# ---------------------------------------------------------------------------
# Small UI helpers
# ---------------------------------------------------------------------------

def section(title: str) -> None:
    print("\n" + "=" * 72)
    print(f"  {title}")
    print("=" * 72)


def info(msg: str) -> None:
    print(f"  • {msg}")


def success(msg: str) -> None:
    print(f"  ✅ {msg}")


def warning(msg: str) -> None:
    print(f"  ⚠️  {msg}")


# ---------------------------------------------------------------------------
# TORMENT client — identical to ryuki_chat.py
# ---------------------------------------------------------------------------

class TormentClient:
    def __init__(self, base_url: str, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.timeout = timeout

    def _post(self, path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        response = self.session.post(
            f"{self.base_url}{path}",
            json=data,
            timeout=self.timeout,
        )
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            raise RuntimeError(
                f"POST {path} failed: {response.status_code} {response.text}"
            ) from e
        return response.json()

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        response = self.session.get(
            f"{self.base_url}{path}",
            params=params or {},
            timeout=self.timeout,
        )
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            raise RuntimeError(
                f"GET {path} failed: {response.status_code} {response.text}"
            ) from e
        return response.json()

    def health(self) -> Dict[str, Any]:
        return self._get("/health")

    def workspace_create(self, ws_id: str, domains: Optional[List[str]] = None) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"workspace_id": ws_id}
        if domains:
            payload["domains"] = domains
        return self._post("/workspace/create", payload)

    def agent_create(self, ws_id: str, agent_id: str, seed: Dict[str, Any]) -> Dict[str, Any]:
        return self._post("/agent/create", {
            "workspace_id": ws_id,
            "agent_id": agent_id,
            "seed": seed,
        })

    def agent_identity(self, ws_id: str, agent_id: str) -> Dict[str, Any]:
        return self._get(f"/agent/{agent_id}/identity", {"workspace_id": ws_id})

    def query(self, ws_id: str, agent_id: str, query: str, top_k: int = 8) -> Dict[str, Any]:
        return self._post("/agent/query", {
            "workspace_id": ws_id,
            "agent_id": agent_id,
            "query": query,
            "top_k": top_k,
        })

    def ingest(self, ws_id: str, agent_id: str, text: str, step: int) -> Dict[str, Any]:
        return self._post("/agent/ingest", {
            "workspace_id": ws_id,
            "agent_id": agent_id,
            "text": text,
            "step": step,
        })

    def spine_submit_task(
        self,
        ws_id: str,
        agent_id: str,
        operation: str,
        payload: Dict[str, Any],
        mode: str = "auto",
    ) -> Dict[str, Any]:
        """POST /spine/submit_task — returns the full governed Spine envelope.

        Used when we want to see decision_code, result_code, drift_status,
        escalated, etc. inline. /tool/ingest only returns the inner result
        dict and raises on failure, so for the probe we use this path.

        Phase-2 caller: /tool local_clock_probe → operation="tool_result_ingest".
        """
        return self._post("/spine/submit_task", {
            "workspace_id": ws_id,
            "agent_id": agent_id,
            "operation": operation,
            "mode": mode,
            "payload": payload,
        })


# ---------------------------------------------------------------------------
# Chat providers
#
# Convention: every provider exposes
#     .name           — short label for UI
#     .model          — model slug
#     .message(system, messages, max_tokens) -> str
# That matches the original ClaudeClient surface in ryuki_chat.py so the
# chat loop body is unchanged.
# ---------------------------------------------------------------------------

class AnthropicProvider:
    """
    Anthropic Messages API client. Mirrors ClaudeClient from ryuki_chat.py
    (SDK if installed, raw requests otherwise). Behavior preserved.
    """

    name = "anthropic"

    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self._sdk = None
        try:
            import anthropic
            self._sdk = anthropic.Anthropic(api_key=api_key)
        except ImportError:
            # Optional dependency — fall back to HTTP.
            pass

    def message(self, system: str, messages: List[Dict[str, str]], max_tokens: int = 1024) -> str:
        if self._sdk:
            resp = self._sdk.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system,
                messages=messages,
            )
            return resp.content[0].text

        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": self.model,
                "max_tokens": max_tokens,
                "system": system,
                "messages": messages,
            },
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()
        return data["content"][0]["text"]


class OpenRouterProvider:
    """
    OpenRouter chat-completions client (OpenAI-compatible).

    Uses the `openai` SDK if installed, otherwise raw requests. Default
    model is `google/gemini-2.5-flash`; can be overridden via
    TORMENT_CHAT_MODEL.

    Note: OpenRouter is the path to Gemini in Phase 1. We do NOT add a
    direct Google/Gemini API client in this phase.
    """

    name = "openrouter"

    def __init__(self, api_key: str, model: str, base_url: str = _OPENROUTER_BASE_URL):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self._sdk = None
        try:
            from openai import OpenAI
            self._sdk = OpenAI(base_url=self.base_url, api_key=self.api_key)
        except ImportError as e:
            log.debug("OpenAI SDK not installed; using raw requests fallback: %s", e)

    def message(self, system: str, messages: List[Dict[str, str]], max_tokens: int = 1024) -> str:
        all_messages = [{"role": "system", "content": system}] + messages

        if self._sdk:
            resp = self._sdk.chat.completions.create(
                model=self.model,
                messages=all_messages,
                max_tokens=max_tokens,
            )
            content = resp.choices[0].message.content
            return content or ""

        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": all_messages,
                "max_tokens": max_tokens,
            },
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()
        choices = data.get("choices", [])
        if not choices:
            raise RuntimeError(
                f"OpenRouter returned no choices: {json.dumps(data)[:300]}"
            )
        return (choices[0].get("message", {}) or {}).get("content", "") or ""


# Type alias for either provider
ChatProvider = Any  # duck-typed: any object with .message(system, messages, max_tokens)


def build_provider() -> ChatProvider:
    """Construct the configured chat provider, or raise with a clear msg."""
    if PROVIDER == "anthropic":
        api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Either export it, or put it in "
                "torment_fabric/.env. (Provider: anthropic)"
            )
        model = PROVIDER_MODEL_OVERRIDE or _ANTHROPIC_DEFAULT_MODEL
        return AnthropicProvider(api_key=api_key, model=model)

    if PROVIDER == "openrouter":
        api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError(
                "OPENROUTER_API_KEY is not set. Either export it, or put it in "
                "torment_fabric/.env. (Provider: openrouter)"
            )
        model = PROVIDER_MODEL_OVERRIDE or _OPENROUTER_DEFAULT_MODEL
        return OpenRouterProvider(api_key=api_key, model=model)

    raise RuntimeError(
        f"Unsupported TORMENT_CHAT_PROVIDER='{PROVIDER}'. "
        "Supported in Phase 1: anthropic, openrouter."
    )


# ---------------------------------------------------------------------------
# Formatting helpers — verbatim from ryuki_chat.py
# ---------------------------------------------------------------------------

def format_memories(hits: List[Dict[str, Any]]) -> str:
    """Format retrieved memory hits into a compact context block."""
    if not hits:
        return ""

    lines = ["[Retrieved memories — most relevant first]"]
    for i, hit in enumerate(hits[:TOP_K], 1):
        summary = hit.get("summary", "")
        score = hit.get("final_score", hit.get("score", 0.0))
        tier = hit.get("character_tier", "")
        prov = hit.get("provenance_type", "")
        tags = " ".join(f"[{x}]" for x in [tier, prov] if x)
        lines.append(f"  {i}. (score {score:.2f}{' ' + tags if tags else ''}) {summary}")
    return "\n".join(lines)


def format_character_context(char_ctx: Dict[str, Any]) -> str:
    """Format the TORMENT character_context block."""
    if not char_ctx:
        return ""

    parts: List[str] = []
    preamble = char_ctx.get("seed_preamble", "")
    if preamble:
        parts.append(f"[Core identity]\n{preamble}")

    recommendations = char_ctx.get("recommendations", [])
    if recommendations:
        parts.append("[Guidance]\n" + "\n".join(f"  - {r}" for r in recommendations))

    return "\n\n".join(parts)


def format_drift_note(char_ctx: Dict[str, Any]) -> str:
    """Create a drift note only when relevant."""
    if not char_ctx:
        return ""

    drift_score = char_ctx.get("drift_score", 0.0)
    drift_summary = char_ctx.get("drift_summary", "")
    if abs(drift_score) < 0.1 and not drift_summary:
        return ""
    return f"[Drift: {drift_score:+.2f}] {drift_summary}"


def print_memory_hits(result: Dict[str, Any]) -> None:
    hits = result.get("hits", result.get("results", []))
    if not hits:
        warning("No hits.")
        return

    print(f"\n--- Memories ({len(hits)} hits) ---")
    for hit in hits:
        summary = hit.get("summary", "?")
        score = hit.get("final_score", hit.get("score", 0.0))
        tier = hit.get("character_tier", "")
        prov = hit.get("provenance_type", "")
        tag = " ".join(x for x in [tier, prov] if x)
        if tag:
            print(f"  [{score:.2f}] {tag:20s} | {summary[:120]}")
        else:
            print(f"  [{score:.2f}] {'':20s} | {summary[:120]}")

    char_ctx = result.get("character_context", {})
    if char_ctx:
        drift_score = char_ctx.get("drift_score", 0.0)
        print(f"  Drift: {drift_score:+.2f}")
    print("---\n")


def print_spine_envelope(envelope: Dict[str, Any]) -> None:
    """Print the Spine governed envelope fields a probe operator cares about.

    Fields shown (per Phase-2 spec):
      ok, path, operation, decision_code, result_code, drift_status,
      escalated, eid (if present in result), reason (only if not ok).

    The full envelope can still be inspected via /debug after a chat turn,
    but the probe printout is intentionally compact.
    """
    ok = envelope.get("ok")
    path = envelope.get("path")
    operation = envelope.get("operation")
    decision_code = envelope.get("decision_code")
    result_code = envelope.get("result_code")
    drift_status = envelope.get("drift_status")
    escalated = envelope.get("escalated")
    reason = envelope.get("reason")

    # eid normally lives inside .result (per MCP_README worked example:
    # {"result": {"eid": 42, "summary": "..."}})
    inner = envelope.get("result") or {}
    eid = inner.get("eid") if isinstance(inner, dict) else None

    section("Spine envelope")
    info(f"ok:            {ok}")
    info(f"path:          {path}")
    info(f"operation:     {operation}")
    info(f"decision_code: {decision_code}")
    info(f"result_code:   {result_code}")
    info(f"drift_status:  {drift_status}")
    info(f"escalated:     {escalated}")
    if eid is not None:
        info(f"eid:           {eid}")
    if not ok and reason:
        info(f"reason:        {reason}")
    print()


def build_summary(user_msg: str, ryuki_reply: str) -> str:
    """
    Compact ingest summary for one turn. Format identical to ryuki_chat.py;
    do not change in Phase 1 — prior memories key on this shape.
    """
    user_short = user_msg[:200].strip()
    ryuki_short = ryuki_reply[:300].strip()

    ryuki_short = ryuki_short.replace("\n\n", "\n").strip()

    return (
        f"Zen said: {user_short}\n"
        f"Ryuki responded: {ryuki_short}"
    )


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

def ensure_setup(torment: TormentClient) -> None:
    """Check server availability and ensure workspace + agent exist."""
    section(f"Initializing {AGENT_ID}")

    try:
        health = torment.health()
        success("TORMENT server reachable.")
        info(f"Server: {TORMENT_URL}")
        if health:
            info("Health endpoint responded.")
    except Exception as e:
        print(f"\n  TORMENT server not reachable at {TORMENT_URL}")
        print(f"  Error: {e}")
        print("\n  Start it first:")
        print("    python -m torment_service.app\n")
        sys.exit(1)

    try:
        torment.workspace_create(WORKSPACE_ID, domains=WORKSPACE_DOMAINS)
        success(f"Workspace '{WORKSPACE_ID}' created.")
    except RuntimeError as e:
        if " 409 " in str(e):
            info(f"Workspace '{WORKSPACE_ID}' already exists.")
        else:
            raise

    try:
        torment.agent_create(WORKSPACE_ID, AGENT_ID, RYUKI_SEED)
        success(f"Agent '{AGENT_ID}' created with default seed.")
    except RuntimeError as e:
        if " 409 " in str(e):
            info(f"Agent '{AGENT_ID}' already exists (using its existing seed).")
        else:
            raise

    try:
        identity = torment.agent_identity(WORKSPACE_ID, AGENT_ID)
        seed_id = identity.get("seed", {}).get("seed_id", "")
        if seed_id:
            info(f"Character seed: {seed_id}")
        else:
            info("Agent active; no seed metadata returned.")
    except Exception:
        info(f"Agent '{AGENT_ID}' active.")


# ---------------------------------------------------------------------------
# Chat loop
# ---------------------------------------------------------------------------

def print_banner(provider: ChatProvider) -> None:
    print("\n" + "=" * 72)
    print(f"  {AGENT_ID} — Live Chat (multi-provider probe)")
    print("=" * 72)
    print(f"  Provider:  {provider.name}")
    print(f"  Model:     {provider.model}")
    print(f"  Workspace: {WORKSPACE_ID}")
    print(f"  Agent:     {AGENT_ID}")
    print(f"  Top-K:     {TOP_K}")
    print(f"  TORMENT:   {TORMENT_URL}")
    print()
    print("  Type your message. 'quit' or 'exit' to leave.")
    print("  /status              — show runtime settings")
    print("  /identity            — show current agent identity")
    print("  /debug               — show last raw query result")
    print("  /memories <query>    — peek at retrieved memories")
    print("  /clear               — clear local chat history only")
    print(f"  /tool <probe_name>   — Phase 2 governed tool-result probe")
    print(f"                         (probes: {LOCAL_CLOCK_PROBE_NAME})")
    print()
    print("  Note: /clear does NOT erase TORMENT memories.")
    print("=" * 72 + "\n")


def chat_loop(torment: TormentClient, provider: ChatProvider) -> None:
    """Main interactive chat loop. Same shape as ryuki_chat.py."""
    step = int(time.time())
    conversation: List[Dict[str, str]] = []
    last_query_result: Dict[str, Any] = {}

    print_banner(provider)

    while True:
        try:
            user_input = input("Zen > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n  ...she turns away without a word.\n")
            break

        if not user_input:
            continue

        lower = user_input.lower()

        if lower in ("quit", "exit"):
            print("\n  ...she turns away without a word.\n")
            break

        # Slash commands
        if lower == "/status":
            section("Runtime status")
            info(f"Provider:         {provider.name}")
            info(f"Model:            {provider.model}")
            info(f"TORMENT_URL:      {TORMENT_URL}")
            info(f"WORKSPACE_ID:     {WORKSPACE_ID}")
            info(f"AGENT_ID:         {AGENT_ID}")
            info(f"TOP_K:            {TOP_K}")
            info(f"Workspace domains: {', '.join(WORKSPACE_DOMAINS)}")
            if _DOTENV_LOADED:
                info(f".env loaded:      {', '.join(_DOTENV_LOADED)}")
            print()
            continue

        if lower == "/identity":
            try:
                identity = torment.agent_identity(WORKSPACE_ID, AGENT_ID)
                section("Agent identity")
                print(json.dumps(identity, indent=2, ensure_ascii=False))
            except Exception as e:
                print(f"  Error fetching identity: {e}\n")
            continue

        if lower == "/debug":
            section("Last query result")
            if not last_query_result:
                warning("No query result yet.")
            else:
                print(json.dumps(last_query_result, indent=2, default=str, ensure_ascii=False))
            print()
            continue

        if lower.startswith("/memories"):
            peek_query = user_input[len("/memories"):].strip() or "recent events"
            try:
                result = torment.query(WORKSPACE_ID, AGENT_ID, peek_query, top_k=TOP_K)
                print_memory_hits(result)
            except Exception as e:
                print(f"  Error: {e}\n")
            continue

        if lower == "/clear":
            conversation.clear()
            print("  Local conversation history cleared. TORMENT memories persist.\n")
            continue

        # /tool <probe_name> — Phase 2 deterministic governed tool-result ingest.
        # The script does NOT execute any external tool. It submits a fixed
        # payload through Spine governance so we can verify the
        # tool_result_ingest path end-to-end. Supported probes are listed in
        # the constants block at the top of this file.
        if lower.startswith("/tool"):
            parts = user_input.split()
            if len(parts) < 2:
                print("\n  Usage: /tool <probe_name>")
                print(f"  Available probes: {LOCAL_CLOCK_PROBE_NAME}\n")
                continue
            probe = parts[1].strip()
            if probe != LOCAL_CLOCK_PROBE_NAME:
                print(f"\n  Unknown probe: {probe!r}")
                print(f"  Available probes: {LOCAL_CLOCK_PROBE_NAME}\n")
                continue

            step += 1
            payload = {
                "tool_name": LOCAL_CLOCK_PROBE_NAME,
                "content": LOCAL_CLOCK_PROBE_CONTENT,
                "summary": LOCAL_CLOCK_PROBE_SUMMARY,
                "domain_id": LOCAL_CLOCK_PROBE_DOMAIN,
                "step": step,
                "scope": "private",
                "session_id": f"probe_{int(time.time())}",
            }
            try:
                envelope = torment.spine_submit_task(
                    WORKSPACE_ID,
                    AGENT_ID,
                    operation="tool_result_ingest",
                    payload=payload,
                )
            except Exception as e:
                print(f"\n  /tool {probe} failed: {e}\n")
                continue

            print_spine_envelope(envelope)
            continue

        # 1) Query TORMENT (identical to ryuki_chat.py)
        try:
            query_result = torment.query(
                WORKSPACE_ID,
                AGENT_ID,
                user_input,
                top_k=TOP_K,
            )
            last_query_result = query_result
        except Exception as e:
            print(f"  [TORMENT query failed: {e} — continuing without memory]\n")
            query_result = {}

        hits = query_result.get("hits", query_result.get("results", []))
        char_ctx = query_result.get("character_context", {})

        # 2) Build system prompt (template identical to ryuki_chat.py)
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            agent_name=AGENT_ID,
            character_context=format_character_context(char_ctx),
            memory_context=format_memories(hits),
            drift_note=format_drift_note(char_ctx),
        ).strip()

        # 3) Send to the configured provider
        conversation.append({"role": "user", "content": user_input})
        if len(conversation) > 40:
            conversation = conversation[-40:]

        try:
            reply = provider.message(
                system=system_prompt,
                messages=conversation,
                max_tokens=1024,
            )
        except Exception as e:
            print(f"  [{provider.name} API error: {e}]\n")
            conversation.pop()
            continue

        conversation.append({"role": "assistant", "content": reply})

        # 4) Show reply
        print(f"\nRyuki > {reply}\n")

        # 5) Ingest compact summary (format and call identical to ryuki_chat.py)
        step += 1
        summary = build_summary(user_input, reply)
        try:
            torment.ingest(WORKSPACE_ID, AGENT_ID, summary, step=step)
        except Exception as e:
            print(f"  [TORMENT ingest failed: {e}]\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    try:
        provider = build_provider()
    except RuntimeError as e:
        print(f"\n  Error: {e}\n")
        print("  NEVER hardcode API keys in files.\n")
        return 1

    torment = TormentClient(TORMENT_URL)

    ensure_setup(torment)
    chat_loop(torment, provider)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
