#!/usr/bin/env python3
"""
check_forge_output.py — Acceptance checker for start/torment_character_creator.html

Validates that each emitted-Python template section in the forge satisfies the doctrinal
and field-shape contracts defined in start/SOLO_ALIGNMENT_SPEC.md §4.

Approach: grep-by-line-range against the HTML source. Each "section" is the JS code inside
a generator function that builds one of the output panes. Line ranges are determined
dynamically by locating the function signatures.

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
#
# Sections we care about:
#   solo      — generateSolo()      (currently fails; being aligned)
#   hivemind  — generateHivemind()  (already patched; window + broadcast both live here)
#
# Basic Hive Agent will add a third section later; the checker picks it up automatically
# once the function exists.

SECTION_SIGNATURES = [
    ("solo",     r"^function generateSolo\s*\("),
    ("hivemind", r"^function generateHivemind\s*\("),
    # Future:
    # ("basic_hive_agent", r"^function generateBasicHiveAgent\s*\("),
]


def find_sections(lines: List[str]) -> Dict[str, Tuple[int, int]]:
    """Return {section_name: (start_line, end_line)} using function signatures.

    end_line is the line before the NEXT known section, or EOF for the last one.
    Line numbers are 1-indexed to match editor/grep conventions.
    """
    starts: List[Tuple[str, int]] = []
    for name, pattern in SECTION_SIGNATURES:
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


# ---------------------------------------------------------------------------
# Guards — §4 of SOLO_ALIGNMENT_SPEC.md
# ---------------------------------------------------------------------------

# Patterns that MUST NOT appear inside a compliant emitted-Python template.
# Each entry: (label, regex, applies_to_sections)
FORBIDDEN: List[Tuple[str, str, List[str]]] = [
    ("wrong memory key `text` preferred",
     r"""h(?:it)?\.get\(\s*["']text["']""",
     ["solo", "hivemind", "basic_hive_agent"]),
    ("wrong char-ctx key `identity_mode`",
     r"""["']identity_mode["']""",
     ["solo", "hivemind", "basic_hive_agent"]),
    ("wrong drift key `drift` (must be drift_score/drift_summary)",
     r"""\.get\(\s*["']drift["']\s*\)""",
     ["solo", "hivemind", "basic_hive_agent"]),
    ("wrong identity path `/character/identity`",
     r"""/character/identity""",
     ["solo", "hivemind", "basic_hive_agent"]),
    ("doctrinal violation: firstLine seed-trait laundering",
     r"""\bfirstLine\b""",
     ["solo", "basic_hive_agent"]),
    ("doctrinal violation: 'Stay true to who you are' scaffolding",
     r"""Stay true to who you are""",
     ["solo", "basic_hive_agent"]),
    ("lazy ingest summary `responded about the topic`",
     r"""responded about the topic""",
     ["solo", "basic_hive_agent"]),
]

# Patterns that MUST appear inside a compliant emitted-Python template.
REQUIRED: List[Tuple[str, str, List[str]]] = [
    ("format_memories reads `summary` key",
     r"""h(?:it)?\.get\(\s*["']summary["']""",
     ["solo", "hivemind", "basic_hive_agent"]),
    ("format_character_context reads `seed_preamble`",
     r"""["']seed_preamble["']""",
     ["solo", "hivemind", "basic_hive_agent"]),
    ("format_character_context reads `recommendations`",
     r"""["']recommendations["']""",
     ["solo", "hivemind", "basic_hive_agent"]),
    ("format_drift_note reads `drift_score`",
     r"""["']drift_score["']""",
     ["solo", "hivemind", "basic_hive_agent"]),
    ("format_drift_note reads `drift_summary`",
     r"""["']drift_summary["']""",
     ["solo", "hivemind", "basic_hive_agent"]),
    ("retrieval tries `hits` before `results`",
     # `hits` must appear at least once in a .get(...) call
     r"""\.get\(\s*["']hits["']""",
     ["solo", "hivemind", "basic_hive_agent"]),
    ("identity endpoint uses `/agent/{id}/identity`",
     r"""/agent/[^/\s"']+/identity(?!\w)""",
     ["solo", "hivemind", "basic_hive_agent"]),
]


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def check_section(name: str, source: str) -> List[str]:
    """Return list of failure messages for this section (empty list == pass)."""
    failures: List[str] = []

    for label, pattern, applies in FORBIDDEN:
        if name not in applies:
            continue
        m = re.search(pattern, source)
        if m:
            # Find line number within section for the hit
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
    sections = find_sections(lines)

    if not sections:
        print("error: no generator sections found — HTML shape changed?", file=sys.stderr)
        return 2

    print(f"Checking {HTML_PATH.name}")
    print(f"Sections discovered: {', '.join(f'{n} [{s}-{e}]' for n, (s, e) in sections.items())}")
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
