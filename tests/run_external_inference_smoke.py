#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tests/run_external_inference_smoke.py

External inference smoke -- Phase 1 (print-only) + Phase 2 (--ingest).

THIS IS AN OPERATOR-RUN SCRIPT, NOT A PYTEST TEST.

It is placed under ``tests/`` because that's the established convention
for operator rigs in this repo (see ``tests/run_geo_compare.py``,
``tests/run_stance_smoke.py``). pytest discovers files matching
``test_*.py``; the ``run_*`` prefix keeps this OUT of normal pytest
runs. The script ALSO defensively refuses to run when pytest is
detected in ``sys.modules`` at startup.

Purpose
-------
Validate the external-inference operational path with the existing
``.env`` setup. One CLI invocation makes ONE provider call with ONE
prompt and prints ONE response. By default no memory ingest happens
and no TORMENT server is required. With ``--ingest`` the response is
forwarded through the sanctioned HTTP write path
``POST /tool/ingest``, which routes through Spine to
``_fast_tool_result_ingest`` -> ``fabric.ingest(...)`` with
``ProvenanceV1.for_tool_result(...)``. No new write path is
introduced; the script never calls ``spawn_memory`` or constructs a
fabric in-process.

What this proves when Phase 1 passes:

* ``.env`` loading works in a non-server context
* the requested provider's SDK is installed
* the API key in ``.env`` is valid for that provider
* the requested model returns a coherent response to a minimal prompt

What ``--ingest`` adds when Phase 2 passes:

* the TORMENT server is reachable on the supplied base URL
* the sanctioned ``/tool/ingest`` route accepts the response and
  returns an ``eid`` for the new memory row

What this does NOT do (both phases):

* does NOT execute tools, only stores their output as memory
* does NOT exercise any character / persona / authoring flow
* does NOT create any writeback path beyond the existing
  sanctioned ``/tool/ingest`` route
* does NOT retry on rate limits or HTTP failures
* does NOT support multi-turn or streaming
* does NOT fetch the resulting row's lifecycle envelope. The
  ``lifecycle_status`` and ``lifecycle_disagreement`` fields are
  surfaced by the MCP ``resource_provenance`` resource, NOT by
  the HTTP ``/debug/provenance`` endpoint. To inspect them after
  ingest, query MCP separately. An HTTP parity slice may follow.

Usage
-----
Phase 1 -- Anthropic (direct), print-only::

    python tests/run_external_inference_smoke.py \\
        --provider anthropic --model claude-sonnet-4-5

Phase 1 -- OpenRouter (Gemini 2.5 Flash, cheapest first smoke)::

    python tests/run_external_inference_smoke.py \\
        --provider openrouter --model google/gemini-2.5-flash

Phase 1 -- custom prompt (capped at 500 chars)::

    python tests/run_external_inference_smoke.py \\
        --provider anthropic --model claude-haiku-4-5 \\
        --prompt "Say only the word: pong"

Phase 2 -- forward the response into TORMENT memory through the
sanctioned ingest route. Requires a running TORMENT server::

    python tests/run_external_inference_smoke.py \\
        --provider openrouter --model google/gemini-2.5-flash \\
        --ingest \\
        --base-url http://127.0.0.1:8787 \\
        --workspace-id default \\
        --agent-id external_inference_smoke

Required environment (loaded from ``.env`` at the repo root if
``python-dotenv`` is available, or otherwise from the process env):

* ``ANTHROPIC_API_KEY``  -- required for ``--provider anthropic``
* ``OPENROUTER_API_KEY`` -- required for ``--provider openrouter``

Server liveness probe (``--ingest`` only)
-----------------------------------------
The script GETs ``{base_url}/health`` before posting. The health
endpoint is defined in ``torment_service/app.py`` and the service
binds to ``http://127.0.0.1:8787`` by default (see
``torment_service/__main__.py``). ``--base-url`` defaults to that
host:port; pass ``--base-url`` to override. If either changes,
update ``DEFAULT_BASE_URL`` / ``HEALTH_PATH`` below.

Exit codes
----------
* 0 -- provider reachable, non-empty response received, no exceptions
       (and with ``--ingest``: server reachable and ``/tool/ingest``
       returned a row with an ``eid``)
* 1 -- any failure: missing key, missing SDK, auth error, model error,
       timeout, empty response, prompt too long, pytest detected,
       unknown provider, server unreachable on ``--ingest``,
       ``/tool/ingest`` non-200, missing ``eid`` in ingest response,
       etc.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import Any, Dict, Optional


DEFAULT_PROMPT = (
    "Reply with exactly one short sentence acknowledging this test prompt."
)
PROMPT_MAX_CHARS = 500
DEFAULT_MAX_TOKENS = 256
DEFAULT_TIMEOUT_SECONDS = 30
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
SUPPORTED_PROVIDERS = ("anthropic", "openrouter")

# --- Phase 2 (--ingest) constants ------------------------------------------
DEFAULT_BASE_URL = "http://127.0.0.1:8787"
DEFAULT_WORKSPACE_ID = "default"
DEFAULT_AGENT_ID = "external_inference_smoke"
HEALTH_PATH = "/health"
INGEST_PATH = "/tool/ingest"
SCRIPT_PHASE_INGEST = "phase_2_ingest"
HEALTH_TIMEOUT_SECONDS = 5
INGEST_TIMEOUT_SECONDS = 30


# ---------------------------------------------------------------------------
# Pytest-refusal
# ---------------------------------------------------------------------------


def _refuse_if_under_pytest() -> None:
    """If pytest is loaded in this process, this script is being run in
    the wrong context. Refuse politely with a clear message.

    Note: the ``run_*`` filename prefix already prevents pytest's
    default discovery from picking up this file, but operators
    sometimes pass scripts explicitly to ``pytest``. This guard
    catches that case.
    """
    if "pytest" in sys.modules:
        print(
            "ERROR: this script is operator-run only. It is not a "
            "pytest test and refuses to run inside pytest. Invoke it "
            "directly with `python tests/run_external_inference_smoke.py`.",
            file=sys.stderr,
        )
        sys.exit(1)


# ---------------------------------------------------------------------------
# .env loading (gracefully degrade if python-dotenv is missing)
# ---------------------------------------------------------------------------


def _load_dotenv_from_repo_root() -> Optional[str]:
    """Try to load ``.env`` from the repo root. Returns the path loaded,
    or ``None`` if python-dotenv isn't installed or no ``.env`` exists.
    Missing python-dotenv is NOT fatal -- env vars can still come from
    the process environment directly.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    env_path = os.path.join(repo_root, ".env")
    if not os.path.exists(env_path):
        return None
    try:
        from dotenv import load_dotenv
    except ImportError:
        return None
    load_dotenv(env_path)
    return env_path


# ---------------------------------------------------------------------------
# Provider call dispatch (lazy SDK imports)
# ---------------------------------------------------------------------------


def _call_anthropic(
    model: str, prompt: str, max_tokens: int, timeout: int,
) -> Dict[str, Any]:
    """Call the Anthropic API. Lazy SDK import."""
    try:
        import anthropic
    except ImportError as exc:
        raise RuntimeError(
            f"anthropic SDK not installed: {exc}. "
            f"Install with: pip install anthropic"
        ) from exc

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY missing. Set it in .env at the repo root "
            "or in the process environment."
        )

    client = anthropic.Anthropic(api_key=api_key, timeout=timeout)
    started = time.time()
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    duration_ms = int((time.time() - started) * 1000)

    # Extract text from the first content block.
    text = ""
    try:
        for block in response.content:
            block_text = getattr(block, "text", None)
            if block_text:
                text += block_text
    except Exception:
        text = ""

    usage = getattr(response, "usage", None)
    input_tokens = getattr(usage, "input_tokens", None) if usage else None
    output_tokens = getattr(usage, "output_tokens", None) if usage else None

    return {
        "text": text,
        "duration_ms": duration_ms,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "finish_reason": getattr(response, "stop_reason", None),
    }


def _call_openrouter(
    model: str, prompt: str, max_tokens: int, timeout: int,
) -> Dict[str, Any]:
    """Call OpenRouter via the OpenAI SDK pointed at OpenRouter's API.
    Lazy SDK import.
    """
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError(
            f"openai SDK not installed: {exc}. "
            f"Install with: pip install openai"
        ) from exc

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY missing. Set it in .env at the repo root "
            "or in the process environment."
        )

    client = OpenAI(
        api_key=api_key, base_url=OPENROUTER_BASE_URL, timeout=timeout,
    )
    started = time.time()
    response = client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    duration_ms = int((time.time() - started) * 1000)

    text = ""
    finish_reason = None
    try:
        if response.choices:
            choice = response.choices[0]
            text = (choice.message.content or "") if choice.message else ""
            finish_reason = getattr(choice, "finish_reason", None)
    except Exception:
        text = ""

    usage = getattr(response, "usage", None)
    input_tokens = getattr(usage, "prompt_tokens", None) if usage else None
    output_tokens = getattr(usage, "completion_tokens", None) if usage else None

    return {
        "text": text,
        "duration_ms": duration_ms,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "finish_reason": finish_reason,
    }


# ---------------------------------------------------------------------------
# Phase 2 -- sanctioned ingest path (HTTP only; no in-process fabric)
# ---------------------------------------------------------------------------
#
# These helpers are exercised ONLY when --ingest is passed. They speak HTTP
# to a running TORMENT server and never touch fabric / spawn_memory / any
# write path other than POST /tool/ingest. stdlib urllib is used to avoid
# adding a runtime dependency.


def _default_tool_name(provider: str, model: str) -> str:
    """Stable, filter-friendly identifier for the tool that produced the row.

    Shape: ``external_inference_smoke:{provider}:{model}``. Operators can
    grep ``nodes.jsonl`` or filter ``/debug/provenance`` on this prefix to
    find smoke-produced rows.
    """
    return f"external_inference_smoke:{provider}:{model}"


def _build_ingest_body(
    *,
    provider: str,
    model: str,
    prompt: str,
    result: Dict[str, Any],
    workspace_id: str,
    agent_id: str,
    tool_name: str,
) -> Dict[str, Any]:
    """Build the JSON body for ``POST /tool/ingest``.

    PURE FUNCTION -- no I/O, no env reads, no SDK calls. Safe to unit-test
    without a server. Mirrors the field shape accepted by
    ``ToolResultIngestReq`` in ``torment_service/app.py`` and only sets
    fields that model already accepts. The server constructs provenance;
    we do not.
    """
    return {
        "workspace_id": workspace_id,
        "agent_id": agent_id,
        "tool_name": tool_name,
        "content": result.get("text", ""),
        "tool_metadata": {
            "provider": provider,
            "model": model,
            "prompt": prompt,
            "duration_ms": result.get("duration_ms"),
            "input_tokens": result.get("input_tokens"),
            "output_tokens": result.get("output_tokens"),
            "finish_reason": result.get("finish_reason"),
            "script_phase": SCRIPT_PHASE_INGEST,
        },
    }


def _server_healthcheck(
    base_url: str, timeout: int = HEALTH_TIMEOUT_SECONDS,
) -> None:
    """GET ``{base_url}/health``. Raise RuntimeError on any failure.

    Caller is expected to translate the RuntimeError into a FAIL line and
    exit 1, matching the rest of the script's error-handling shape.
    """
    import urllib.error
    import urllib.request

    url = base_url.rstrip("/") + HEALTH_PATH
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = getattr(resp, "status", resp.getcode())
            if int(status) != 200:
                raise RuntimeError(
                    f"server health check at {url} returned status "
                    f"{status}; start TORMENT server first"
                )
    except urllib.error.HTTPError as exc:
        raise RuntimeError(
            f"server not reachable at {base_url}; start TORMENT server "
            f"first (HTTP {exc.code} on {HEALTH_PATH})"
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"server not reachable at {base_url}; start TORMENT server "
            f"first ({exc.reason})"
        ) from exc
    except Exception as exc:
        raise RuntimeError(
            f"server not reachable at {base_url}; start TORMENT server "
            f"first ({type(exc).__name__}: {exc})"
        ) from exc


def _post_ingest(
    base_url: str, body: Dict[str, Any], timeout: int = INGEST_TIMEOUT_SECONDS,
) -> Dict[str, Any]:
    """POST ``body`` as JSON to ``{base_url}/tool/ingest``.

    Returns the parsed response dict on HTTP 200. Raises RuntimeError on
    anything else (non-200, malformed JSON, network failure). No retries.
    """
    import urllib.error
    import urllib.request

    url = base_url.rstrip("/") + INGEST_PATH
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = getattr(resp, "status", resp.getcode())
            raw = resp.read().decode("utf-8", errors="replace")
            if int(status) != 200:
                raise RuntimeError(
                    f"POST {url} returned status {status}: {raw[:500]}"
                )
            try:
                return json.loads(raw)
            except json.JSONDecodeError as exc:
                raise RuntimeError(
                    f"POST {url} returned non-JSON body: {raw[:500]}"
                ) from exc
    except urllib.error.HTTPError as exc:
        body_text = ""
        try:
            if exc.fp is not None:
                body_text = exc.read().decode("utf-8", errors="replace")
        except Exception:
            body_text = ""
        raise RuntimeError(
            f"POST {url} returned HTTP {exc.code}: {body_text[:500]}"
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"POST {url} failed: {exc.reason}") from exc


def _print_ingest_result(
    workspace_id: str,
    agent_id: str,
    tool_name: str,
    response: Any,
) -> None:
    """Print the Phase-2 ingest receipt block. Lifecycle envelope NOT fetched."""
    eid = response.get("eid") if isinstance(response, dict) else None
    print()
    print("--- Ingest result ---")
    print(f"  workspace_id:   {workspace_id}")
    print(f"  agent_id:       {agent_id}")
    print(f"  tool_name:      {tool_name}")
    print(f"  eid:            "
          f"{eid if eid is not None else '(not in response)'}")
    print(f"  raw response:   {response!r}")
    print("---------------------")
    print()
    print("Lifecycle envelope: not fetched in Phase 2.")
    print(
        "  Use MCP `resource_provenance` to inspect lifecycle_status and "
        "lifecycle_disagreement for the resulting row."
    )
    print()


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------


def _print_header(provider: str, model: str, prompt: str) -> None:
    print("=== TORMENT external inference smoke ===")
    print(f"Provider:   {provider}")
    print(f"Model:      {model}")
    print(f"Prompt:     {prompt!r}")
    print()


def _print_response(result: Dict[str, Any]) -> None:
    print("Sending request...")
    print()
    print("--- Response ---")
    print(result["text"] or "(empty)")
    print("----------------")
    print()
    print("Metadata:")
    print(f"  duration_ms:    {result['duration_ms']}")
    if result.get("input_tokens") is not None:
        print(f"  input_tokens:   {result['input_tokens']}")
    if result.get("output_tokens") is not None:
        print(f"  output_tokens:  {result['output_tokens']}")
    if result.get("finish_reason") is not None:
        print(f"  finish_reason:  {result['finish_reason']}")
    print()
    print("Lifecycle envelope: (skipped -- Phase 1 does not ingest)")
    print()


# ---------------------------------------------------------------------------
# Main entry
# ---------------------------------------------------------------------------


def _parse_args(argv: Optional[list] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "External inference smoke -- Phase 1 (print-only) + Phase 2 "
            "(--ingest, posts to TORMENT /tool/ingest). "
            "Operator-run only; not a pytest test."
        ),
    )
    parser.add_argument(
        "--provider", required=True, choices=SUPPORTED_PROVIDERS,
        help="Provider to call: anthropic (direct) or openrouter.",
    )
    parser.add_argument(
        "--model", required=True,
        help=(
            "Provider-specific model slug. "
            "Anthropic example: claude-sonnet-4-5 or claude-haiku-4-5. "
            "OpenRouter example: google/gemini-2.5-flash."
        ),
    )
    parser.add_argument(
        "--prompt", default=DEFAULT_PROMPT,
        help=(
            f"Prompt to send. Default: a minimal acknowledgement prompt. "
            f"Maximum {PROMPT_MAX_CHARS} chars."
        ),
    )
    parser.add_argument(
        "--max-tokens", type=int, default=DEFAULT_MAX_TOKENS,
        help=f"Max response tokens. Default: {DEFAULT_MAX_TOKENS}.",
    )
    parser.add_argument(
        "--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS,
        help=f"Per-request timeout in seconds. Default: {DEFAULT_TIMEOUT_SECONDS}.",
    )

    # --- Phase 2 (--ingest) options. Default off. -------------------------
    parser.add_argument(
        "--ingest", action="store_true",
        help=(
            "PHASE 2: after the provider call, POST the response to the "
            "TORMENT server's sanctioned ingest route (/tool/ingest). "
            "Requires a running server. Off by default; with this flag the "
            "script becomes a write-path smoke."
        ),
    )
    parser.add_argument(
        "--base-url", default=DEFAULT_BASE_URL,
        help=(
            f"Base URL of the running TORMENT server. Only used with "
            f"--ingest. Default: {DEFAULT_BASE_URL}."
        ),
    )
    parser.add_argument(
        "--workspace-id", default=DEFAULT_WORKSPACE_ID,
        help=(
            f"Workspace to ingest into. Only used with --ingest. "
            f"Default: {DEFAULT_WORKSPACE_ID!r}."
        ),
    )
    parser.add_argument(
        "--agent-id", default=DEFAULT_AGENT_ID,
        help=(
            f"Agent to ingest under. Only used with --ingest. The server "
            f"will defensively create the agent if it does not exist. "
            f"Default: {DEFAULT_AGENT_ID!r}."
        ),
    )
    parser.add_argument(
        "--tool-name", default=None,
        help=(
            "Override the tool_name attached to the ingested row. Only "
            "used with --ingest. Default: "
            "'external_inference_smoke:{provider}:{model}'."
        ),
    )
    return parser.parse_args(argv)


def main(argv: Optional[list] = None) -> int:
    _refuse_if_under_pytest()

    args = _parse_args(argv)

    if len(args.prompt) > PROMPT_MAX_CHARS:
        print(
            f"ERROR: prompt is {len(args.prompt)} chars; max is "
            f"{PROMPT_MAX_CHARS}. Use a shorter prompt to avoid "
            f"surprise API costs.",
            file=sys.stderr,
        )
        return 1

    loaded_env = _load_dotenv_from_repo_root()

    _print_header(args.provider, args.model, args.prompt)
    if loaded_env:
        print(f"(.env loaded from {loaded_env})")
        print()

    try:
        if args.provider == "anthropic":
            result = _call_anthropic(
                model=args.model,
                prompt=args.prompt,
                max_tokens=args.max_tokens,
                timeout=args.timeout,
            )
        elif args.provider == "openrouter":
            result = _call_openrouter(
                model=args.model,
                prompt=args.prompt,
                max_tokens=args.max_tokens,
                timeout=args.timeout,
            )
        else:
            # argparse should reject this before we get here; defensive.
            print(
                f"ERROR: unknown provider {args.provider!r}",
                file=sys.stderr,
            )
            return 1
    except RuntimeError as exc:
        # Our own raised errors -- API key missing, SDK missing, etc.
        print(f"FAIL  -- {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        # Any other exception from the SDK / network / API.
        print(
            f"FAIL  -- {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 1

    _print_response(result)

    if not result["text"]:
        print(
            "FAIL  -- empty response from provider",
            file=sys.stderr,
        )
        return 1

    if args.ingest:
        tool_name = args.tool_name or _default_tool_name(
            args.provider, args.model,
        )
        try:
            _server_healthcheck(args.base_url)
        except RuntimeError as exc:
            print(f"FAIL  -- {exc}", file=sys.stderr)
            return 1

        body = _build_ingest_body(
            provider=args.provider,
            model=args.model,
            prompt=args.prompt,
            result=result,
            workspace_id=args.workspace_id,
            agent_id=args.agent_id,
            tool_name=tool_name,
        )
        try:
            ingest_response = _post_ingest(args.base_url, body)
        except RuntimeError as exc:
            print(f"FAIL  -- {exc}", file=sys.stderr)
            return 1

        _print_ingest_result(
            workspace_id=args.workspace_id,
            agent_id=args.agent_id,
            tool_name=tool_name,
            response=ingest_response,
        )

        if not isinstance(ingest_response, dict) or not ingest_response.get(
            "eid"
        ):
            print(
                "FAIL  -- ingest response missing 'eid'; the row may not "
                "have been written. Raw response above.",
                file=sys.stderr,
            )
            return 1

        print(
            "PASS  -- provider reachable, response received, ingested "
            "via /tool/ingest, eid returned"
        )
        return 0

    print(
        "PASS  -- provider reachable, response received, no exceptions"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
