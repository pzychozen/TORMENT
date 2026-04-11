# torment_service/migration/cli.py
"""
CLI entry point for ``torment-migration``.

Commit A ships **only** the read-only commands:

  - ``dry-run``  — classify every row in a row-source stream, emit the
                   four-section report to stdout or an output file,
                   optionally bookkeep into ``.torment_migration/cursor.jsonl``.
  - ``status``   — read the cursor and review queue under
                   ``.torment_migration/`` and print counts.

There is **no** ``apply`` command in commit A. Attempting to invoke a
write-path command MUST exit non-zero with a clear error. The
implementation plan commits to adding ``apply`` only in commit B, under
its own review.

The CLI does not read the corpus directly. Commit A is corpus-agnostic
— the row-source must be supplied via ``--rows-from-jsonl`` (a caller-
produced JSONL file where each line is a ``{"eid": int,
"provenance": <raw>}`` object). This keeps the CLI testable without a
real storage layer and gives the operator full control over which
rows are scanned. Commit B will add a ``--from-workspace`` mode that
plugs into the real corpus.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Iterator, List, Optional, Tuple

from .cursor import processed_eids, read_entries
from .dry_run import DryRunReport, run_dry_run
from .review_queue import read_reviews


def _row_stream_from_jsonl(path: str) -> Iterator[Tuple[int, Any]]:
    """Yield ``(eid, raw_provenance)`` tuples from a JSONL input file.

    Each line must be a JSON object with at least an ``eid`` field and
    a ``provenance`` field. Extra keys are ignored. Blank lines are
    skipped.
    """
    with open(path, "r", encoding="utf-8") as f:
        for line_num, raw_line in enumerate(f, start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"{path}:{line_num}: invalid JSON line: {exc}"
                )
            if "eid" not in obj:
                raise ValueError(
                    f"{path}:{line_num}: missing required 'eid' field"
                )
            yield (int(obj["eid"]), obj.get("provenance"))


def _cmd_dry_run(args: argparse.Namespace) -> int:
    rows = _row_stream_from_jsonl(args.rows_from_jsonl)
    report = run_dry_run(
        rows,
        workspace_root=args.workspace_root,
        write_cursor=bool(args.write_cursor),
        skip_processed=bool(args.resume),
    )
    out = report.to_json(indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out)
            f.write("\n")
    else:
        sys.stdout.write(out)
        sys.stdout.write("\n")
    return 0


def _cmd_status(args: argparse.Namespace) -> int:
    root = args.workspace_root
    if not root:
        sys.stderr.write("error: --workspace-root is required for status\n")
        return 2
    cursor_entries = read_entries(root)
    reviews = read_reviews(root)
    summary = {
        "workspace_root": os.path.abspath(root),
        "cursor_entries": len(cursor_entries),
        "review_queue_entries": len(reviews),
        "processed_eid_count": len(processed_eids(root)),
    }
    sys.stdout.write(json.dumps(summary, indent=2))
    sys.stdout.write("\n")
    return 0


def _cmd_apply_blocked(args: argparse.Namespace) -> int:
    """Commit A has no apply path. This handler exists so an invocation
    of ``torment-migration apply`` exits with a clear error, rather
    than looking like the argparse 'unknown command' failure mode
    (which can be mistaken for a missing install)."""
    sys.stderr.write(
        "error: 'apply' is not available in commit A of step 6. "
        "Commit A ships dry-run only. See "
        "docs/WRITE_MIGRATION_IMPLEMENTATION_PLAN_v2.4.x.md for the "
        "commit A / commit B split.\n"
    )
    return 3


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="torment-migration",
        description=(
            "WRITE_MIGRATION tooling for TORMENT v2.4.x step 6. "
            "Commit A ships dry-run + status only; no write path."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # dry-run
    p_dry = sub.add_parser(
        "dry-run",
        help="Classify rows and produce the four-section dry-run report",
    )
    p_dry.add_argument(
        "--rows-from-jsonl",
        required=True,
        help="Path to a JSONL file; each line must contain {eid, provenance}",
    )
    p_dry.add_argument(
        "--workspace-root",
        default=None,
        help="Workspace root for .torment_migration/ cursor and review queue",
    )
    p_dry.add_argument(
        "--write-cursor",
        action="store_true",
        help="Append cursor entries so the dry-run itself is resumable",
    )
    p_dry.add_argument(
        "--resume",
        action="store_true",
        help="Skip rows with an existing cursor entry (requires --write-cursor)",
    )
    p_dry.add_argument(
        "-o", "--output",
        default=None,
        help="Write report to this path instead of stdout",
    )
    p_dry.set_defaults(func=_cmd_dry_run)

    # status
    p_status = sub.add_parser(
        "status",
        help="Summarise cursor + review queue state under a workspace",
    )
    p_status.add_argument(
        "--workspace-root",
        required=True,
        help="Workspace root for .torment_migration/",
    )
    p_status.set_defaults(func=_cmd_status)

    # apply (blocked in commit A)
    p_apply = sub.add_parser(
        "apply",
        help="(not available in commit A — use dry-run)",
    )
    p_apply.set_defaults(func=_cmd_apply_blocked)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
