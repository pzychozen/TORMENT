# torment_service/migration/cli.py
"""
CLI entry point for ``torment-migration``.

Commands
--------

  - ``dry-run``  — classify every row in a row-source stream, emit the
                   four-section report to stdout or an output file,
                   optionally bookkeep into ``.torment_migration/cursor.jsonl``.
  - ``status``   — read the cursor and review queue under
                   ``.torment_migration/`` and print counts.
  - ``apply``    — **commit B writer path.** Runs the wet-run
                   orchestrator over a row-source stream and rewrites
                   each admissible row. Gated behind an explicit
                   ``--confirm-i-have-reviewed-dry-run`` flag so an
                   operator cannot accidentally write without having
                   looked at the dry-run report first.

The CLI is corpus-agnostic at the ``dry-run`` and ``apply`` entry
points — the row-source must be supplied via ``--rows-from-jsonl`` (a
caller-produced JSONL file where each line is a ``{"eid": int,
"provenance": <raw>}`` object). This keeps the CLI testable without a
real storage layer and gives the operator full control over which
rows are scanned. A ``--from-workspace`` mode that plugs into a live
``MemoryGraph`` is deliberately deferred to a post-step-6 commit.

For ``apply``, the CLI needs a mutable graph target. A file-backed
stub is loaded from the same JSONL rows: each ``(eid, raw)`` tuple
becomes a ``_FileBackedEntity``, ``update_payload`` merges patches
into an in-memory dict, and at the end of the run the updated rows
are written back to a user-specified ``--output-jsonl`` path. This
keeps commit B's write path observable without requiring a real
``MemoryGraph`` construction in the CLI.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, List, Optional, Tuple

from .cursor import processed_eids, read_entries
from .dry_run import run_dry_run
from .review_queue import read_reviews
from .wet_run import run_wet_run


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


# ── File-backed graph stub for ``apply`` ────────────────────────────
#
# The apply command needs a mutable graph target but the CLI is
# corpus-agnostic. This stub is loaded from the same JSONL shape
# ``dry-run`` already consumes: each row becomes a
# ``_FileBackedEntity`` whose payload carries the raw provenance in
# the same slot the wet-run orchestrator expects. ``update_payload``
# merges patches into the in-memory dict; at the end of the run the
# caller writes every row (touched or not) back to
# ``--output-jsonl`` so the patched state is inspectable.


@dataclass
class _FileBackedEntity:
    payload: Dict[str, Any] = field(default_factory=dict)


class _FileBackedGraph:
    """A mutable ``graph`` stub that satisfies the wet_run contract
    without touching any real corpus. Loaded from a JSONL stream and
    serialisable back to JSONL."""

    def __init__(self) -> None:
        self.entities: Dict[int, _FileBackedEntity] = {}

    @classmethod
    def load_from_jsonl(cls, path: str) -> "_FileBackedGraph":
        g = cls()
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
                eid = int(obj["eid"])
                payload: Dict[str, Any] = {}
                if "provenance" in obj:
                    payload["provenance"] = obj["provenance"]
                g.entities[eid] = _FileBackedEntity(payload=payload)
        return g

    def update_payload(self, eid: int, patch: Dict[str, Any]) -> None:
        if eid not in self.entities:
            raise KeyError(eid)
        self.entities[eid].payload.update(dict(patch))

    def dump_to_jsonl(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            for eid in sorted(self.entities.keys()):
                ent = self.entities[eid]
                obj: Dict[str, Any] = {"eid": int(eid)}
                if "provenance" in ent.payload:
                    obj["provenance"] = ent.payload["provenance"]
                f.write(json.dumps(obj, ensure_ascii=False))
                f.write("\n")


def _cmd_apply(args: argparse.Namespace) -> int:
    """Run the commit-B writer path.

    Gated behind ``--confirm-i-have-reviewed-dry-run``. This is a
    deliberate operator-side friction: no wet-run may start without
    the operator affirming they have looked at the dry-run report
    first. The flag name is verbose on purpose — it is the piece of
    the command line a reviewer can grep for to verify compliance.
    """
    if not args.confirm_i_have_reviewed_dry_run:
        sys.stderr.write(
            "error: 'apply' requires --confirm-i-have-reviewed-dry-run. "
            "Run 'torment-migration dry-run' first, review the report, "
            "then re-invoke with the confirmation flag.\n"
        )
        return 3

    if not args.workspace_root:
        sys.stderr.write(
            "error: --workspace-root is required for apply\n"
        )
        return 2

    graph = _FileBackedGraph.load_from_jsonl(args.rows_from_jsonl)

    def _iter_rows() -> Iterator[Tuple[int, Any]]:
        for eid in sorted(graph.entities.keys()):
            raw = graph.entities[eid].payload.get("provenance")
            yield (int(eid), raw)

    report = run_wet_run(
        graph,
        _iter_rows(),
        workspace_root=args.workspace_root,
        skip_processed=bool(args.resume),
    )

    if args.output_jsonl:
        graph.dump_to_jsonl(args.output_jsonl)

    include_rows = bool(args.report_include_rows)
    out = report.to_json(indent=2, include_rows=include_rows)
    if args.report_output:
        with open(args.report_output, "w", encoding="utf-8") as f:
            f.write(out)
            f.write("\n")
    else:
        sys.stdout.write(out)
        sys.stdout.write("\n")
    return 0


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

    # apply (commit B writer path)
    p_apply = sub.add_parser(
        "apply",
        help=(
            "Rewrite admissible rows to canonical provenance. "
            "Requires --confirm-i-have-reviewed-dry-run."
        ),
    )
    p_apply.add_argument(
        "--rows-from-jsonl",
        required=True,
        help="Path to a JSONL file; each line must contain {eid, provenance}",
    )
    p_apply.add_argument(
        "--workspace-root",
        required=True,
        help=(
            "Workspace root for .torment_migration/ cursor and review "
            "queue. Required for apply because the writer appends cursor "
            "entries on every successful row write."
        ),
    )
    p_apply.add_argument(
        "--output-jsonl",
        default=None,
        help=(
            "Write the updated graph state back to this path. Omit to "
            "run apply without persisting the rewritten rows (useful "
            "for comparing a run against a shared workspace cursor)."
        ),
    )
    p_apply.add_argument(
        "--report-output",
        default=None,
        help="Write wet-run report to this path instead of stdout",
    )
    p_apply.add_argument(
        "--report-include-rows",
        action="store_true",
        help=(
            "Include the per-row outcome list in the report. Off by "
            "default because it can be large; counters are always "
            "included."
        ),
    )
    p_apply.add_argument(
        "--resume",
        action="store_true",
        help=(
            "Skip rows with an existing cursor entry. The writer's "
            "precondition-6 cross-check still runs on non-skipped rows."
        ),
    )
    p_apply.add_argument(
        "--confirm-i-have-reviewed-dry-run",
        action="store_true",
        help=(
            "Required acknowledgement that the operator has reviewed the "
            "four-section dry-run report before invoking the writer. "
            "Without this flag, apply exits non-zero without touching "
            "any row."
        ),
    )
    p_apply.set_defaults(func=_cmd_apply)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
