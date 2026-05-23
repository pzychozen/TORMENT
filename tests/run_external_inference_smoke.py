#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tests/run_external_inference_smoke.py

External inference smoke -- Phase 1 (print-only).

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
prompt and prints ONE response. No memory ingest, no TORMENT server
dependency, no autonomy loop, no multi-turn conversation.

What this proves when it passes:

* ``.env`` loading works in a non-server context
* the requested provider's SDK is installed
* the API key in ``.env`` is valid for that provider
* the requested model returns a coherent response to a minimal prompt

What this does NOT do:

* does NOT ingest the response into TORMENT memory
* does NOT require the TORMENT server to be running
* does NOT exercise any character / persona / authoring flow
* does NOT create any writeback path
* does NOT retry on rate limits

Phase 2 (separate future slice -- not implemented here): may add an
opt-in ``--ingest`` flag that routes the response through the
existing sanctioned ``tool_result_ingest`` path and prints the
resulting row's lifecycle envelope. Phase 2 would require the
TORMENT server to be running and would be its own ratifiable slice.

Usage
-----
Anthropic (direct)::

    python tests/run_external_inference_smoke.py \\
        --provider anthropic --model claude-sonnet-4-5

OpenRouter (Gemini 2.5 Flash, typically the cheapest first smoke)::

    python tests/run_external_inference_smoke.py \\
        --provider openrouter --model google/gemini-2.5-flash

With a custom prompt (capped at 500 chars)::

    python tests/run_external_inference_smoke.py \\
        --provider anthropic --model claude-haiku-4-5 \\
        --prompt "Say only the word: pong"

Required environment (loaded from ``.env`` at the repo root if
``python-dotenv`` is available, or otherwise from the process env):

* ``ANTHROPIC_API_KEY``  -- required for ``--provider anthropic``
* ``OPENROUTER_API_KEY`` -- required for ``--provider openrouter``

Exit codes
----------
* 0 -- provider reachable, non-empty response received, no exceptions
* 1 -- any failure: missing key, missing SDK, auth error, model error,
       timeout, empty response, prompt too long, pytest detected,
       unknown provider, etc.
"""
from __future__ import annotations

import argparse
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
            "External inference smoke -- Phase 1 (print-only). "
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

    print(
        "PASS  -- provider reachable, response received, no exceptions"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
