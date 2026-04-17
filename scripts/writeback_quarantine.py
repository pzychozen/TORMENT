#!/usr/bin/env python3
"""
writeback_quarantine.py — Post-rollback quarantine tool (D5 deliverable)

Identifies all memories produced by archivist writeback (write_path =
"cognition_writeback") and can list, tag, or remove them.

Modes:
    --list      Show all writeback-origin entities (default).
    --tag       Mark each writeback entity's provenance with
                {"quarantined": true, "quarantined_ts": <iso>}.
    --remove    Delete writeback entities from nodes.jsonl by appending a
                tombstone record (payload=null, alive=false).

Safety:
    --tag and --remove require --confirm to execute. Without --confirm
    they run in dry-run mode showing what would change.

The script operates directly on nodes.jsonl files (same append-only
semantics as MemoryGraph). No running service required.

Exit codes:
    0 — completed successfully.
    1 — error or unexpected condition.

Usage:
    python scripts/writeback_quarantine.py --list [--data-dir data/]
    python scripts/writeback_quarantine.py --tag  [--data-dir data/] [--confirm]
    python scripts/writeback_quarantine.py --remove [--data-dir data/] [--confirm]

Reference:
    docs/ARCHIVIST_WRITEBACK_GATE_FRAMING_v2.4.x.md §6.4, §7 D5
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple


# ---------------------------------------------------------------------------
# JSONL loading — same pattern as writeback_guard_reverify.py
# ---------------------------------------------------------------------------

def load_entities_from_jsonl(nodes_path: Path) -> Dict[int, Dict[str, Any]]:
    """Load nodes.jsonl, returning {eid: full_record} with last-record-wins."""
    entities: Dict[int, Dict[str, Any]] = {}
    if not nodes_path.exists():
        return entities
    with nodes_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            eid = obj.get("eid")
            if eid is None:
                continue
            entities[int(eid)] = obj
    return entities


def discover_agents(data_dir: Path) -> List[Tuple[str, str, Path]]:
    """Return [(workspace_id, agent_id, nodes_jsonl_path), ...]."""
    ws_root = data_dir / "workspaces"
    if not ws_root.exists():
        return []
    agents: List[Tuple[str, str, Path]] = []
    for ws_name in sorted(os.listdir(ws_root)):
        agents_root = ws_root / ws_name / "agents"
        if not agents_root.exists():
            continue
        for agent_id in sorted(os.listdir(agents_root)):
            nodes_path = agents_root / agent_id / "private" / "nodes.jsonl"
            if nodes_path.exists():
                agents.append((ws_name, agent_id, nodes_path))
    return agents


# ---------------------------------------------------------------------------
# Writeback entity detection
# ---------------------------------------------------------------------------

WRITEBACK_WRITE_PATH = "cognition_writeback"
WRITEBACK_SOURCE_ROLE = "archivist_writeback"


def is_writeback_entity(record: Dict[str, Any]) -> bool:
    """Return True if the entity was produced by archivist writeback."""
    payload = record.get("payload") or {}
    prov = payload.get("provenance") or {}
    if not isinstance(prov, dict):
        return False
    return (
        prov.get("write_path") == WRITEBACK_WRITE_PATH
        or prov.get("source_role") == WRITEBACK_SOURCE_ROLE
    )


# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------

def action_list(
    agents: List[Tuple[str, str, Path]],
) -> int:
    """List all writeback entities across all workspaces."""
    total = 0
    for ws_id, ag_id, nodes_path in agents:
        entities = load_entities_from_jsonl(nodes_path)
        wb_eids = [eid for eid, rec in sorted(entities.items())
                   if is_writeback_entity(rec)]
        if wb_eids:
            print(f"  {ws_id}/{ag_id}: {len(wb_eids)} writeback entities")
            for eid in wb_eids:
                payload = entities[eid].get("payload", {})
                prov = payload.get("provenance", {})
                summary = (payload.get("summary") or "")[:80]
                print(f"    eid={eid}  write_path={prov.get('write_path')}  "
                      f"source_role={prov.get('source_role')}  "
                      f"summary={summary!r}")
            total += len(wb_eids)
        else:
            print(f"  {ws_id}/{ag_id}: 0 writeback entities")
    print(f"\nTotal writeback entities: {total}")
    return 0


def action_tag(
    agents: List[Tuple[str, str, Path]],
    confirm: bool,
) -> int:
    """Tag writeback entities with quarantined=true."""
    now_iso = datetime.now(timezone.utc).isoformat()
    total_tagged = 0

    for ws_id, ag_id, nodes_path in agents:
        entities = load_entities_from_jsonl(nodes_path)
        wb_records = [(eid, rec) for eid, rec in sorted(entities.items())
                      if is_writeback_entity(rec)]
        if not wb_records:
            continue

        print(f"  {ws_id}/{ag_id}: {len(wb_records)} to tag")
        if not confirm:
            for eid, _ in wb_records:
                print(f"    [dry-run] would tag eid={eid}")
            total_tagged += len(wb_records)
            continue

        # Append tagged records to nodes.jsonl
        with nodes_path.open("a", encoding="utf-8") as f:
            for eid, rec in wb_records:
                tagged = copy.deepcopy(rec)
                prov = tagged.setdefault("payload", {}).setdefault("provenance", {})
                prov["quarantined"] = True
                prov["quarantined_ts"] = now_iso
                f.write(json.dumps(tagged, separators=(",", ":")) + "\n")
                print(f"    tagged eid={eid}")
        total_tagged += len(wb_records)

    mode = "tagged" if confirm else "would tag"
    print(f"\nTotal {mode}: {total_tagged}")
    if not confirm and total_tagged > 0:
        print("  (pass --confirm to apply)")
    return 0


def action_remove(
    agents: List[Tuple[str, str, Path]],
    confirm: bool,
) -> int:
    """Remove writeback entities by appending tombstone records."""
    total_removed = 0

    for ws_id, ag_id, nodes_path in agents:
        entities = load_entities_from_jsonl(nodes_path)
        wb_records = [(eid, rec) for eid, rec in sorted(entities.items())
                      if is_writeback_entity(rec)]
        if not wb_records:
            continue

        print(f"  {ws_id}/{ag_id}: {len(wb_records)} to remove")
        if not confirm:
            for eid, _ in wb_records:
                print(f"    [dry-run] would remove eid={eid}")
            total_removed += len(wb_records)
            continue

        # Append tombstone records (payload=null, alive=false)
        with nodes_path.open("a", encoding="utf-8") as f:
            for eid, rec in wb_records:
                tombstone = {
                    "eid": eid,
                    "born_step": rec.get("born_step", 0),
                    "channel": rec.get("channel", 0),
                    "payload": None,
                    "alive": False,
                }
                f.write(json.dumps(tombstone, separators=(",", ":")) + "\n")
                print(f"    removed eid={eid}")
        total_removed += len(wb_records)

    mode = "removed" if confirm else "would remove"
    print(f"\nTotal {mode}: {total_removed}")
    if not confirm and total_removed > 0:
        print("  (pass --confirm to apply)")
    return 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Post-rollback quarantine tool for writeback entities (D5)")
    parser.add_argument(
        "--data-dir", type=str, default="data",
        help="Path to the TORMENT data directory (default: data/)")

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--list", action="store_true", default=True,
                      help="List all writeback entities (default)")
    mode.add_argument("--tag", action="store_true",
                      help="Tag writeback entities with quarantined=true")
    mode.add_argument("--remove", action="store_true",
                      help="Remove writeback entities via tombstone records")

    parser.add_argument("--confirm", action="store_true",
                        help="Required for --tag and --remove to actually write")

    args = parser.parse_args()
    data_dir = Path(args.data_dir).resolve()

    if not data_dir.exists():
        print(f"error: data directory not found: {data_dir}", file=sys.stderr)
        return 1

    agents = discover_agents(data_dir)
    if not agents:
        print(f"No workspaces/agents found under {data_dir}/workspaces/")
        return 0

    print(f"Writeback quarantine — scanning {len(agents)} agent graph(s)\n")

    if args.remove:
        return action_remove(agents, args.confirm)
    elif args.tag:
        return action_tag(agents, args.confirm)
    else:
        return action_list(agents)


if __name__ == "__main__":
    raise SystemExit(main())
