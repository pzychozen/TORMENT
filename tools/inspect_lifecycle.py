#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tools/inspect_lifecycle.py

Read-only inspector for the Q2 lifecycle envelope on existing memory
rows. Reports ``lifecycle_status`` and ``lifecycle_disagreement`` for
each selected row, computed via the canonical helpers in
``torment_service.lifecycle``.

THIS IS AN OPERATOR-RUN SCRIPT, NOT A PYTEST TEST.

It lives under ``tools/`` alongside the other operator rigs
(``tools/verify.py``, ``tools/run_coherence_field.py``). pytest
discovers files matching ``test_*.py``; the ``inspect_*`` prefix keeps
this OUT of normal pytest runs. The script ALSO defensively refuses to
run when pytest is detected in ``sys.modules`` at startup.

Purpose
-------
Verify Q2-D operational expectations on real memory rows already on
disk. The classic post-Phase-2 use case:

    workspace_id = default
    agent_id     = external_inference_smoke
    eid          = 1, 2

Expected envelope shape for vanilla external tool-result rows:

* ``state = unset``
* ``is_authoritative_on_row = true``
* ``requires_join = null``
* ``set_by.actor = system``
* ``set_by.via = ingest_unmarked``
* ``history_ref = null``
* ``lifecycle_disagreement = null``

What this proves when it runs cleanly
-------------------------------------
* the rows have a parseable ``payload`` on disk
* the lifecycle helpers produce a canonical envelope on each payload
* the Q2-D disagreement detector returns ``None`` on rows that have
  no legacy protected markers and a clean stamped envelope

What this does NOT do
---------------------
* does NOT mutate any file (read-only on ``nodes.jsonl``)
* does NOT boot a ``TormentFabric`` instance
* does NOT start any HTTP or MCP server
* does NOT make any API or provider calls
* does NOT require the TORMENT server to be running, but is safe to
  run while it is -- ``nodes.jsonl`` is append-only, so reading it
  needs no lock
* does NOT add any new HTTP endpoint, MCP resource, or write path
* does NOT exit non-zero on a detected lifecycle disagreement; the
  disagreement is surfaced as a *finding*, not a failure (parse or
  helper errors still exit 1)

Usage
-----
Inspect specific eids::

    python tools/inspect_lifecycle.py \\
        --workspace-id default \\
        --agent-id external_inference_smoke \\
        --eids 1,2

Inspect the most recent ``--limit`` rows (default 10)::

    python tools/inspect_lifecycle.py \\
        --workspace-id default \\
        --agent-id external_inference_smoke

Emit JSON for piping to ``jq`` or for diffing later::

    python tools/inspect_lifecycle.py \\
        --workspace-id default \\
        --agent-id external_inference_smoke \\
        --eids 1,2 \\
        --json

Override the data directory (useful for testing against a snapshot)::

    python tools/inspect_lifecycle.py \\
        --workspace-id default \\
        --agent-id external_inference_smoke \\
        --data-dir C:\\path\\to\\snapshot\\data

On-disk format
--------------
``nodes.jsonl`` is one JSON record per line, append-only, written by
``MemoryGraph.flush_node``::

    {"eid": <int>, "born_step": <int>, "channel": <int>, "payload": {...}}

This script reads the file once, builds a dict ``{eid: payload}`` with
last-record-wins semantics (matching ``MemoryGraph._load``), and runs
the lifecycle helpers on each selected payload.

Exit codes
----------
* 0 -- inspection succeeded; results printed
* 1 -- any failure: missing nodes.jsonl, parse error, requested eid
       not found, helper exception, pytest detected
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Path setup -- allow importing from torment_service when run from repo root
# ---------------------------------------------------------------------------

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


# Default data dir mirrors ``torment_service/app.py``'s computation
# (``os.environ.get("TORMENT_DATA_DIR", os.path.join(__file__-dir, "..", "data"))``).
# Operators can override with ``--data-dir``.
DEFAULT_DATA_DIR = os.path.normpath(os.path.join(_REPO_ROOT, "data"))
DEFAULT_LIMIT = 10


# ---------------------------------------------------------------------------
# Pytest-refusal
# ---------------------------------------------------------------------------


def _refuse_if_under_pytest() -> None:
    """Refuse cleanly if pytest is loaded in this process.

    The ``inspect_*`` filename prefix already prevents pytest's
    default discovery from picking up this file, but operators
    sometimes pass scripts explicitly to ``pytest``. Guard against
    that.
    """
    if "pytest" in sys.modules:
        print(
            "ERROR: this script is operator-run only. It is not a "
            "pytest test and refuses to run inside pytest. Invoke it "
            "directly with `python tools/inspect_lifecycle.py`.",
            file=sys.stderr,
        )
        sys.exit(1)


# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------


def _nodes_jsonl_path(data_dir: str, workspace_id: str, agent_id: str) -> str:
    """Compute the canonical nodes.jsonl path for one private graph.

    Mirrors ``torment_service/app.py:1488-1493``:
    ``<data_dir>/workspaces/<workspace_id>/agents/<agent_id>/private/nodes.jsonl``
    """
    return os.path.join(
        data_dir, "workspaces", workspace_id, "agents", agent_id,
        "private", "nodes.jsonl",
    )


# ---------------------------------------------------------------------------
# JSONL reading with last-record-wins semantics
# ---------------------------------------------------------------------------


def _read_nodes_jsonl(path: str) -> Dict[int, Dict[str, Any]]:
    """Read ``nodes.jsonl`` and return ``{eid: payload}`` with the LAST
    record for each eid winning -- matches ``MemoryGraph._load``.

    Raises RuntimeError with a clear message on file-not-found or
    parse errors so the caller can translate to exit 1.
    """
    if not os.path.exists(path):
        raise RuntimeError(
            f"no nodes.jsonl found at {path}; check --workspace-id, "
            f"--agent-id, and --data-dir"
        )

    out: Dict[int, Dict[str, Any]] = {}
    with open(path, "r", encoding="utf-8") as f:
        for line_no, raw in enumerate(f, start=1):
            line = raw.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                raise RuntimeError(
                    f"malformed JSON on line {line_no} of {path}: {exc}"
                ) from exc
            try:
                eid = int(obj.get("eid"))
            except (TypeError, ValueError) as exc:
                raise RuntimeError(
                    f"missing or invalid 'eid' on line {line_no} of "
                    f"{path}: {exc}"
                ) from exc
            payload = obj.get("payload") or {}
            if not isinstance(payload, dict):
                raise RuntimeError(
                    f"'payload' on line {line_no} of {path} is not a "
                    f"JSON object (got {type(payload).__name__})"
                )
            out[eid] = payload
    return out


# ---------------------------------------------------------------------------
# Selection (--eids vs --limit)
# ---------------------------------------------------------------------------


def _parse_eids_arg(eids_arg: Optional[str]) -> Optional[List[int]]:
    """Parse the ``--eids`` comma-separated value into a list of ints.

    Returns None if ``--eids`` was not provided. Raises RuntimeError
    on malformed input.
    """
    if eids_arg is None:
        return None
    parts = [p.strip() for p in eids_arg.split(",")]
    out: List[int] = []
    for p in parts:
        if not p:
            continue
        try:
            out.append(int(p))
        except ValueError as exc:
            raise RuntimeError(
                f"--eids: expected comma-separated integers, got {p!r}"
            ) from exc
    if not out:
        raise RuntimeError("--eids: no valid integers parsed")
    return out


def _select_rows(
    all_rows: Dict[int, Dict[str, Any]],
    eids: Optional[List[int]],
    limit: int,
) -> List[Tuple[int, Dict[str, Any]]]:
    """Pick the rows to inspect.

    If ``eids`` is provided, returns rows in the order eids were
    given, raising RuntimeError if any requested eid is missing.
    Otherwise returns the ``limit`` most recent rows (sorted by eid
    descending).
    """
    if eids is not None:
        missing = [e for e in eids if e not in all_rows]
        if missing:
            raise RuntimeError(
                f"requested eid(s) not found in nodes.jsonl: "
                f"{', '.join(str(m) for m in missing)}"
            )
        return [(e, all_rows[e]) for e in eids]
    sorted_eids = sorted(all_rows.keys(), reverse=True)[:limit]
    return [(e, all_rows[e]) for e in sorted_eids]


# ---------------------------------------------------------------------------
# Lifecycle helper invocation + serialization
# ---------------------------------------------------------------------------


def _compute_lifecycle_for_row(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Run the canonical lifecycle helpers on a single payload dict.

    Returns a dict with two keys:

    * ``lifecycle_status``: dict from ``LifecycleStatus.to_dict()``
    * ``lifecycle_disagreement``: dict OR ``None``

    The disagreement dataclass has no ``to_dict``; serialize manually.
    """
    # Late import to keep import cost off the script if --help is the
    # only thing being asked for.
    from torment_service.lifecycle import (
        read_lifecycle_envelope,
        detect_lifecycle_legacy_marker_disagreement,
    )

    envelope = read_lifecycle_envelope(payload)
    disagreement = detect_lifecycle_legacy_marker_disagreement(payload)

    disagreement_dict: Optional[Dict[str, Any]] = None
    if disagreement is not None:
        disagreement_dict = {
            "kind": disagreement.kind.value,
            "explicit_state": disagreement.explicit_state.value,
            "explicit_is_authoritative_on_row":
                disagreement.explicit_is_authoritative_on_row,
            "explicit_via": disagreement.explicit_via.value,
            "derived_via": disagreement.derived_via.value,
        }

    return {
        "lifecycle_status": envelope.to_dict(),
        "lifecycle_disagreement": disagreement_dict,
    }


def _provenance_context(payload: Dict[str, Any]) -> Dict[str, Optional[str]]:
    """Extract a small provenance summary for human-readable display."""
    prov = payload.get("provenance")
    if not isinstance(prov, dict):
        return {
            "source_type": None,
            "write_path": None,
            "tool_name": None,
        }
    return {
        "source_type": prov.get("source_type"),
        "write_path": prov.get("write_path"),
        "tool_name": prov.get("tool_name"),
    }


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------


def _print_header(
    workspace_id: str, agent_id: str, data_dir: str, nodes_path: str,
    rows_total: int, eids_shown: int,
) -> None:
    print("=== TORMENT lifecycle inspector ===")
    print(f"workspace_id:   {workspace_id}")
    print(f"agent_id:       {agent_id}")
    print(f"data_dir:       {data_dir}")
    print(f"nodes_path:     {nodes_path}")
    print(f"rows_total:     {rows_total}  (eids shown: {eids_shown})")
    print()


def _print_row(
    eid: int,
    provenance: Dict[str, Optional[str]],
    lifecycle: Dict[str, Any],
) -> None:
    status = lifecycle["lifecycle_status"]
    disagreement = lifecycle["lifecycle_disagreement"]
    set_by = status.get("set_by") or {}
    history_ref = status.get("history_ref")
    requires_join = status.get("requires_join")

    print(f"--- eid={eid} ---")
    print(f"  source_type:                {provenance['source_type']!r}")
    print(f"  write_path:                 {provenance['write_path']!r}")
    print(f"  tool_name:                  {provenance['tool_name']!r}")
    print(f"  lifecycle_status:")
    print(f"    state:                      {status.get('state')!r}")
    print(
        f"    is_authoritative_on_row:    "
        f"{status.get('is_authoritative_on_row')}"
    )
    print(f"    requires_join:              {requires_join}")
    print(f"    set_by.actor:               {set_by.get('actor')!r}")
    print(f"    set_by.via:                 {set_by.get('via')!r}")
    print(f"    set_by.at:                  {set_by.get('at')}")
    print(f"    history_ref:                {history_ref}")
    if disagreement is None:
        print(f"  lifecycle_disagreement:     null")
    else:
        print(f"  lifecycle_disagreement:")
        for k, v in disagreement.items():
            print(f"    {k}: {v!r}")
    print()


def _print_summary(rows: List[Dict[str, Any]]) -> None:
    """Print a small machine-checkable summary block at the end."""
    if not rows:
        print("=== Summary ===")
        print("(no rows inspected)")
        print()
        return

    all_unset_system_ingest = all(
        (r["lifecycle"]["lifecycle_status"].get("state") == "unset")
        and (
            (r["lifecycle"]["lifecycle_status"].get("set_by") or {}).get(
                "actor"
            ) == "system"
        )
        and (
            (r["lifecycle"]["lifecycle_status"].get("set_by") or {}).get(
                "via"
            ) == "ingest_unmarked"
        )
        for r in rows
    )
    any_disagreement = any(
        r["lifecycle"]["lifecycle_disagreement"] is not None for r in rows
    )
    print("=== Summary ===")
    print(
        f"all_lifecycle_unset_system_ingest_unmarked:   "
        f"{str(all_unset_system_ingest).lower()}"
    )
    print(
        f"any_disagreement_detected:                    "
        f"{str(any_disagreement).lower()}"
    )
    print()


# ---------------------------------------------------------------------------
# Main entry
# ---------------------------------------------------------------------------


def _parse_args(argv: Optional[list] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only inspector for the Q2 lifecycle envelope on "
            "existing memory rows. Operator-run only; not a pytest test."
        ),
    )
    parser.add_argument(
        "--workspace-id", required=True,
        help="Workspace whose memory rows to inspect.",
    )
    parser.add_argument(
        "--agent-id", required=True,
        help=(
            "Agent within the workspace whose private graph to inspect."
        ),
    )
    parser.add_argument(
        "--eids", default=None,
        help=(
            "Comma-separated eids to inspect (e.g. '1,2,3'). If omitted, "
            f"the most recent --limit rows are shown."
        ),
    )
    parser.add_argument(
        "--limit", type=int, default=DEFAULT_LIMIT,
        help=(
            f"Max rows to inspect when --eids is not provided. "
            f"Default: {DEFAULT_LIMIT}."
        ),
    )
    parser.add_argument(
        "--data-dir", default=DEFAULT_DATA_DIR,
        help=(
            f"Override the TORMENT data directory. Default: the repo's "
            f"./data (computed relative to this script). Current default "
            f"resolves to: {DEFAULT_DATA_DIR}"
        ),
    )
    parser.add_argument(
        "--json", action="store_true",
        help=(
            "Emit a single JSON document instead of human-readable "
            "blocks. Pipeable to jq."
        ),
    )
    return parser.parse_args(argv)


def main(argv: Optional[list] = None) -> int:
    _refuse_if_under_pytest()

    args = _parse_args(argv)

    if args.limit < 1:
        print(
            f"ERROR: --limit must be >= 1, got {args.limit}",
            file=sys.stderr,
        )
        return 1

    try:
        eids = _parse_eids_arg(args.eids)
    except RuntimeError as exc:
        print(f"FAIL  -- {exc}", file=sys.stderr)
        return 1

    nodes_path = _nodes_jsonl_path(
        args.data_dir, args.workspace_id, args.agent_id,
    )

    try:
        all_rows = _read_nodes_jsonl(nodes_path)
    except RuntimeError as exc:
        print(f"FAIL  -- {exc}", file=sys.stderr)
        return 1

    try:
        selected = _select_rows(all_rows, eids, args.limit)
    except RuntimeError as exc:
        print(f"FAIL  -- {exc}", file=sys.stderr)
        return 1

    # Compute per-row lifecycle. Catch helper failures cleanly.
    computed_rows: List[Dict[str, Any]] = []
    for eid, payload in selected:
        try:
            lifecycle = _compute_lifecycle_for_row(payload)
        except Exception as exc:
            print(
                f"FAIL  -- lifecycle helpers raised on eid={eid}: "
                f"{type(exc).__name__}: {exc}",
                file=sys.stderr,
            )
            return 1
        computed_rows.append({
            "eid": eid,
            "provenance": _provenance_context(payload),
            "lifecycle": lifecycle,
        })

    if args.json:
        out_doc = {
            "workspace_id": args.workspace_id,
            "agent_id": args.agent_id,
            "data_dir": args.data_dir,
            "nodes_path": nodes_path,
            "rows_total": len(all_rows),
            "eids_shown": len(computed_rows),
            "rows": computed_rows,
        }
        print(json.dumps(out_doc, indent=2, default=str))
        return 0

    # Human output
    _print_header(
        workspace_id=args.workspace_id,
        agent_id=args.agent_id,
        data_dir=args.data_dir,
        nodes_path=nodes_path,
        rows_total=len(all_rows),
        eids_shown=len(computed_rows),
    )
    for r in computed_rows:
        _print_row(
            eid=r["eid"],
            provenance=r["provenance"],
            lifecycle=r["lifecycle"],
        )
    _print_summary(computed_rows)
    return 0


if __name__ == "__main__":
    sys.exit(main())
