#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Offline regression coverage for the Probe-v0 clean model-visible prompt surface.

HARNESS-ONLY. No service, no network, no model call. Pins the narrow
seed_canon exclusion in run_bounded_loop.extract_plain_memory_lines and the
downstream build_clean_prompt / fact_present contract it feeds.

Why this exists: under companion run 20260531T181119Z_c1c2 the decomposed
seed_canon fragments re-entered "Things you remember:" after the verbatim seed
was already placed once at the top, confounding the probe. The fix excludes
is_seed AND type=="seed_canon".

Codex correction pinned by test_runtime_core_episode_retained: the exclusion
must NOT key on source == "core" — the planted runtime episode is serialized as
core material too, so a source-based filter would drop the chapter-seven fact.

Run directly:   python character_memory_harness/test_prompt_surface_offline.py
Or via pytest:  pytest character_memory_harness/test_prompt_surface_offline.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from run_bounded_loop import (  # noqa: E402
    extract_plain_memory_lines,
    build_clean_prompt,
    fact_present,
    _strip_presentation_labels,
)

# --- fixtures mirroring real /retrieve block shapes (from c1c2 forensics) -----

SEED_TEXT = (
    "You are Eland, a scholar who has been wrong enough times to find\n"
    "correction more interesting than being right. You reach for clean\n"
    "answers before the world is finished giving them."
)
FACT = "chapter-seven festival = spring of the second year (not the first)"
TEMP_FACT = "chapter-seven festival = spring of the second year (not the first)"
LEAD_IN = "Things you remember:"


def _seed_block():
    """Verbatim seed identity block, marked is_seed by the service."""
    return {
        "block_type": "identity_context",
        "text": "[Character: Eland]\n" + SEED_TEXT + "\n[Drift: score=0.000, direction=stable]",
        "source": "core",
        "metadata": {"is_seed": True},
    }


def _seed_canon_block(text):
    """Decomposed seed fragment: source=='core', type=='seed_canon' (NOT is_seed)."""
    return {
        "block_type": "identity_context",
        "text": text,
        "source": "core",
        "metadata": {"type": "seed_canon", "half_life": 3650.0, "strength": 0.95},
    }


def _runtime_episode_block():
    """The planted chapter-seven fact. source=='core' too, but type=='episode'."""
    return {
        "block_type": "relational_context",
        "text": FACT,
        "source": "core",
        "metadata": {"type": "episode", "half_life": 96.4, "provenance_type": "user_input"},
    }


def _plain_identity_memory_block():
    """A legitimate non-seed identity memory (not seed_canon, not is_seed)."""
    return {
        "block_type": "identity_context",
        "text": "[Character: Eland]\nYou prefer working at dusk.",
        "source": "core",
        "metadata": {"type": "episode"},
    }


def _resp(*blocks):
    out = {}
    for b in blocks:
        out.setdefault(b["block_type"], []).append(b)
    return {"blocks": out}


# --- the 8 pinned cases -------------------------------------------------------

def test_is_seed_block_excluded():
    assert extract_plain_memory_lines(_resp(_seed_block())) == []


def test_seed_canon_block_excluded():
    block = _seed_canon_block("You sometimes complete a pattern too early.")
    assert extract_plain_memory_lines(_resp(block)) == []


def test_runtime_core_episode_retained():
    # Codex correction: source=="core" must NOT be the filter; type=="episode" survives.
    assert extract_plain_memory_lines(_resp(_runtime_episode_block())) == [FACT]


def test_plain_identity_memory_retained():
    lines = extract_plain_memory_lines(_resp(_plain_identity_memory_block()))
    assert lines == ["You prefer working at dusk."], lines


def test_label_stripping_preserves_plain_text():
    block = {
        "block_type": "identity_context",
        "text": "[Voice: warm]\nThe page where a name looked certain.",
        "source": "core",
        "metadata": {"type": "episode"},
    }
    assert extract_plain_memory_lines(_resp(block)) == ["The page where a name looked certain."]
    # direct check on the stripper: label line dropped, content preserved verbatim
    assert _strip_presentation_labels("[Drift: score=0]\nkept verbatim") == ["kept verbatim"]


def test_seed_only_prompt_seed_once_no_memory_section():
    resp = _resp(
        _seed_block(),
        _seed_canon_block("You reach for clean answers before the world is finished."),
        _seed_canon_block("You sometimes complete a pattern too early."),
    )
    lines = extract_plain_memory_lines(resp)
    assert lines == [], lines
    prompt = build_clean_prompt(SEED_TEXT, lines, LEAD_IN)
    assert LEAD_IN not in prompt, "seed-only prompt must not carry an empty memory section"
    assert prompt.count("You are Eland") == 1, "seed must appear exactly once"
    assert prompt == SEED_TEXT.rstrip()


def test_runtime_prompt_seed_once_and_fact_once():
    resp = _resp(
        _seed_block(),
        _seed_canon_block("You reach for clean answers before the world is finished."),
        _runtime_episode_block(),
    )
    lines = extract_plain_memory_lines(resp)
    assert lines == [FACT], lines
    prompt = build_clean_prompt(SEED_TEXT, lines, LEAD_IN)
    assert prompt.count("You are Eland") == 1, "seed must appear exactly once"
    assert prompt.count(FACT) == 1, "planted fact must appear exactly once"
    assert LEAD_IN in prompt


def test_fact_present_false_seed_only_true_runtime():
    seed_only = extract_plain_memory_lines(
        _resp(_seed_block(), _seed_canon_block("You reach for clean answers."))
    )
    runtime = extract_plain_memory_lines(
        _resp(_seed_block(), _seed_canon_block("frag"), _runtime_episode_block())
    )
    assert fact_present(seed_only, TEMP_FACT) is False
    assert fact_present(runtime, TEMP_FACT) is True


_TESTS = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]

if __name__ == "__main__":
    failures = 0
    for t in _TESTS:
        try:
            t()
            print(f"PASS  {t.__name__}")
        except AssertionError as exc:
            failures += 1
            print(f"FAIL  {t.__name__}: {exc}")
    print(f"\n{len(_TESTS) - failures}/{len(_TESTS)} passed")
    raise SystemExit(1 if failures else 0)
