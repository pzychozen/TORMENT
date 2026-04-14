#!/usr/bin/env python3
"""
check_forge_output.py — Acceptance checker for start/torment_character_creator.html

Validates that each emitted-Python template section in the forge satisfies the doctrinal
and field-shape contracts defined in start/SOLO_ALIGNMENT_SPEC.md §4 and
start/BASIC_HIVE_AGENT_SPEC.md §4.

Section discovery:
    - solo                  — function generateSolo(...)        [function signature]
    - hivemind_window       — fence comments inside generateHivemind
    - hivemind_basic_hive   — fence comments inside generateHivemind
    - hivemind_broadcast    — fence comments inside generateHivemind

Manual use only. No pre-commit wiring yet.

Exit codes:
    0 — all sections pass.
    1 — at least one guard tripped.
    2 — parse error (HTML shape changed; update this script).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

HTML_PATH = Path(__file__).resolve().parent.parent / "start" / "torment_character_creator.html"


# ---------------------------------------------------------------------------
# Section discovery
# ---------------------------------------------------------------------------

FUNCTION_SIGNATURES = [
    ("solo",     r"^function generateSolo\s*\("),
    ("hivemind", r"^function generateHivemind\s*\("),
]

# Fence-comment sub-sections inside generateHivemind.
# Each entry: (section_name, begin_fence_regex, end_fence_regex)
HIVEMIND_FENCES = [
    ("hivemind_window",     r"//\s*<<<\s*BEGIN\s+window\s*>>>",     r"//\s*<<<\s*END\s+window\s*>>>"),
    ("hivemind_basic_hive", r"//\s*<<<\s*BEGIN\s+basic_hive\s*>>>", r"//\s*<<<\s*END\s+basic_hive\s*>>>"),
    ("hivemind_broadcast",  r"//\s*<<<\s*BEGIN\s+broadcast\s*>>>",  r"//\s*<<<\s*END\s+broadcast\s*>>>"),
]


def find_function_sections(lines: List[str]) -> Dict[str, Tuple[int, int]]:
    """Return {section_name: (start_line, end_line)} for top-level generator functions."""
    starts: List[Tuple[str, int]] = []
    for name, pattern in FUNCTION_SIGNATURES:
        pat = re.compile(pattern)
        for i, ln in enumerate(lines, 1):
            if pat.search(ln):
                starts.append((name, i))
                break
    if not starts:
        return {}

    starts.sort(key=lambda x: x[1])
    sections: Dict[str, Tuple[int, int]] = {}
    for idx, (name, start) in enumerate(starts):
        end = starts[idx + 1][1] - 1 if idx + 1 < len(starts) else len(lines)
        sections[name] = (start, end)
    return sections


def find_fence_sections(
    lines: List[str], outer: Tuple[int, int]
) -> Dict[str, Tuple[int, int]]:
    """Within outer (start_line, end_line), locate each fenced sub-section."""
    outer_start, outer_end = outer
    found: Dict[str, Tuple[int, int]] = {}
    for name, begin_re, end_re in HIVEMIND_FENCES:
        begin_pat = re.compile(begin_re)
        end_pat = re.compile(end_re)
        begin_ln: int | None = None
        end_ln: int | None = None
        for i in range(outer_start, outer_end + 1):
            ln = lines[i - 1]
            if begin_ln is None and begin_pat.search(ln):
                begin_ln = i
                continue
            if begin_ln is not None and end_pat.search(ln):
                end_ln = i
                break
        if begin_ln is not None and end_ln is not None:
            found[name] = (begin_ln, end_ln)
    return found


# ---------------------------------------------------------------------------
# Guards
# ---------------------------------------------------------------------------

ALL_SECTIONS = ["solo", "hivemind_window", "hivemind_basic_hive", "hivemind_broadcast"]
DOCTRINAL_SOLO_LIKE = ["solo", "hivemind_basic_hive"]  # no /switch laundering applies
FIELD_SHAPE_ALL = ALL_SECTIONS  # all emitted Python must speak the TORMENT shapes

# Patterns that MUST NOT appear.
# Entry: (label, regex, applies_to_sections)
FORBIDDEN: List[Tuple[str, str, List[str]]] = [
    # ---- shared field-shape contracts (SOLO_ALIGNMENT_SPEC §4) ----
    ("wrong memory key `text` preferred",
     r"""h(?:it)?\.get\(\s*["']text["']""",
     FIELD_SHAPE_ALL),
    ("wrong char-ctx key `identity_mode`",
     r"""["']identity_mode["']""",
     FIELD_SHAPE_ALL),
    ("wrong drift key `drift` (must be drift_score/drift_summary)",
     r"""\.get\(\s*["']drift["']\s*\)""",
     FIELD_SHAPE_ALL),
    ("wrong identity path `/character/identity`",
     r"""/character/identity""",
     FIELD_SHAPE_ALL),
    ("doctrinal violation: firstLine seed-trait laundering",
     r"""\bfirstLine\b""",
     DOCTRINAL_SOLO_LIKE),
    ("doctrinal violation: 'Stay true to who you are' scaffolding",
     r"""Stay true to who you are""",
     DOCTRINAL_SOLO_LIKE),
    ("lazy ingest summary `responded about the topic`",
     r"""responded about the topic""",
     DOCTRINAL_SOLO_LIKE),

    # ---- basic_hive mode (BASIC_HIVE_AGENT_SPEC §4d) ----
    ("basic_hive must not expose /switch slash command",
     r'''if\s+op\s*==\s*["\']/switch["\']''',
     ["hivemind_basic_hive"]),
    ("basic_hive must not expose /agents slash command",
     r'''if\s+op\s*==\s*["\']/agents["\']''',
     ["hivemind_basic_hive"]),
    ("basic_hive must not expose /help slash command",
     r'''if\s+op\s*==\s*["\']/help["\']''',
     ["hivemind_basic_hive"]),
    ("basic_hive --agent must be required (no default=sorted(AGENTS.keys))",
     r"""default=sorted\(AGENTS\.keys""",
     ["hivemind_basic_hive"]),
    ("basic_hive banner must not advertise /switch command",
     r"""/switch\s+<agent_id>""",
     ["hivemind_basic_hive"]),

    # ---- broadcast mode (BASIC_HIVE_AGENT_SPEC §4c) ----
    ("broadcast must not expose /switch slash command",
     r'''if\s+op\s*==\s*["\']/switch["\']''',
     ["hivemind_broadcast"]),
]

# Patterns that MUST appear.
REQUIRED: List[Tuple[str, str, List[str]]] = [
    # ---- shared field-shape contracts ----
    ("format_memories reads `summary` key",
     r"""h(?:it)?\.get\(\s*["']summary["']""",
     FIELD_SHAPE_ALL),
    ("format_character_context reads `seed_preamble`",
     r"""["']seed_preamble["']""",
     FIELD_SHAPE_ALL),
    ("format_character_context reads `recommendations`",
     r"""["']recommendations["']""",
     FIELD_SHAPE_ALL),
    ("format_drift_note reads `drift_score`",
     r"""["']drift_score["']""",
     FIELD_SHAPE_ALL),
    ("format_drift_note reads `drift_summary`",
     r"""["']drift_summary["']""",
     FIELD_SHAPE_ALL),
    ("retrieval tries `hits` before `results`",
     r"""\.get\(\s*["']hits["']""",
     FIELD_SHAPE_ALL),
    # Identity endpoint: solo/window/basic_hive talk to one agent and call
    # /agent/{id}/identity directly. Broadcast reads character_context from
    # the per-query response instead — no identity endpoint needed there.
    ("identity endpoint uses `/agent/{id}/identity`",
     r"""/agent/[^/\s"']+/identity(?!\w)""",
     ["solo", "hivemind_window", "hivemind_basic_hive"]),

    # ---- hivemind shared (COLLECTIVE_ROSTER) ----
    ("hivemind scripts include COLLECTIVE_ROSTER block",
     r"""COLLECTIVE_ROSTER\s*=\s*textwrap\.dedent""",
     ["hivemind_window", "hivemind_basic_hive", "hivemind_broadcast"]),

    # ---- window mode (BASIC_HIVE_AGENT_SPEC §4b) ----
    ("window mode exposes /switch slash command",
     r'''if\s+op\s*==\s*["\']/switch["\']''',
     ["hivemind_window"]),
    ("window mode exposes /agents slash command",
     r'''if\s+op\s*==\s*["\']/agents["\']''',
     ["hivemind_window"]),
    ("window mode --agent defaults to first agent",
     r"""default=sorted\(AGENTS\.keys\(\)\)\[0\]""",
     ["hivemind_window"]),

    # ---- basic_hive mode (BASIC_HIVE_AGENT_SPEC §4d) ----
    ("basic_hive --agent is required=True",
     r"""required\s*=\s*True""",
     ["hivemind_basic_hive"]),
    ("basic_hive banner/docstring mentions 'one terminal per agent' or 'basic'",
     r"""(?:one terminal per agent|Basic Hive Agent|basic mode)""",
     ["hivemind_basic_hive"]),

    # ---- broadcast mode (BASIC_HIVE_AGENT_SPEC §4c) ----
    ("broadcast iterates AGENTS.items() for broadcast loop",
     r"""for\s+\w+\s*,\s*\w+\s+in\s+AGENTS\.items\(\)""",
     ["hivemind_broadcast"]),
    ("broadcast banner mentions Broadcast or every agent",
     r"""(?:Broadcast|every agent)""",
     ["hivemind_broadcast"]),
]


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def check_section(name: str, source: str) -> List[str]:
    failures: List[str] = []

    for label, pattern, applies in FORBIDDEN:
        if name not in applies:
            continue
        m = re.search(pattern, source)
        if m:
            prefix = source[: m.start()]
            rel_line = prefix.count("\n") + 1
            failures.append(
                f"  FORBIDDEN matched: {label}\n"
                f"    pattern: {pattern}\n"
                f"    hit (~section line {rel_line}): {m.group(0)!r}"
            )

    for label, pattern, applies in REQUIRED:
        if name not in applies:
            continue
        if not re.search(pattern, source):
            failures.append(
                f"  REQUIRED missing: {label}\n"
                f"    pattern: {pattern}"
            )

    return failures


def main() -> int:
    if not HTML_PATH.exists():
        print(f"error: forge HTML not found at {HTML_PATH}", file=sys.stderr)
        return 2

    text = HTML_PATH.read_text(encoding="utf-8")
    lines = text.splitlines()

    fn_sections = find_function_sections(lines)
    if "solo" not in fn_sections or "hivemind" not in fn_sections:
        print("error: generateSolo or generateHivemind not found — HTML shape changed?",
              file=sys.stderr)
        return 2

    fence_sections = find_fence_sections(lines, fn_sections["hivemind"])
    expected_fenced = {"hivemind_window", "hivemind_basic_hive", "hivemind_broadcast"}
    missing_fences = expected_fenced - set(fence_sections.keys())
    if missing_fences:
        print(f"error: missing fence sub-sections inside generateHivemind: "
              f"{sorted(missing_fences)}", file=sys.stderr)
        return 2

    sections: Dict[str, Tuple[int, int]] = {
        "solo": fn_sections["solo"],
        **fence_sections,
    }

    print(f"Checking {HTML_PATH.name}")
    for n, (s, e) in sections.items():
        print(f"  section {n}: lines {s}-{e}")
    print()

    all_pass = True
    for name, (start, end) in sections.items():
        source = "\n".join(lines[start - 1:end])
        failures = check_section(name, source)
        if failures:
            all_pass = False
            print(f"[FAIL] {name} (lines {start}-{end}):")
            for f in failures:
                print(f)
            print()
        else:
            print(f"[PASS] {name} (lines {start}-{end})")

    print()
    if all_pass:
        print("All sections pass.")
        return 0
    print("One or more sections failed. See above.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
