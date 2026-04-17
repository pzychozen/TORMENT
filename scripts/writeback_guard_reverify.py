#!/usr/bin/env python3
"""
writeback_guard_reverify.py — Pre-gate-flip guard re-verification (D2 deliverable)

Scans every workspace/agent private graph under data/workspaces/ and runs
recursion_guard_check against every entity. Proves the guard correctly admits
or rejects the entire live corpus before TORMENT_ARCHIVIST_WRITEBACK is
flipped on.

The script reads nodes.jsonl directly (last record per EID wins) and builds
an in-process lookup_fn — no running service required.

Exit codes:
    0 — all workspaces pass (zero guard failures on well-formed provenance).
    1 — at least one guard failure.
    2 — parse or I/O error.

Usage:
    python scripts/writeback_guard_reverify.py [--data-dir data/]

Reference:
    docs/ARCHIVIST_WRITEBACK_GATE_FRAMING_v2.4.x.md §6.1, §7 D2
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Import guard + provenance from the project
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from cognition.recursion_guard import (  # noqa: E402
    REASON_MIGRATION_REFUSED,
    recursion_guard_check,
)
from torment_service.provenance_v1 import (  # noqa: E402
    SOURCE_GATE1_UNRECOVERABLE,
)


# ---------------------------------------------------------------------------
# JSONL loading (same last-record-wins semantics as MemoryGraph._load)
# ---------------------------------------------------------------------------

def load_entities_from_jsonl(nodes_path: Path) -> Dict[int, Dict[str, Any]]:
    """Load nodes.jsonl, returning {eid: payload} with last-record-wins."""
    entities: Dict[int, Dict[str, Any]] = {}
    if not nodes_path.exists():
        return entities
    with nodes_path.open("r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                print(f"  WARNING: malformed JSON at {nodes_path}:{lineno}: {exc}",
                      file=sys.stderr)
                continue
            eid = obj.get("eid")
            if eid is None:
                continue
            payload = obj.get("payload", {})
            entities[int(eid)] = payload
    return entities


# ---------------------------------------------------------------------------
# Workspace / agent discovery
# ---------------------------------------------------------------------------

def discover_agents(data_dir: Path) -> List[Tuple[str, str, Path]]:
    """Return [(workspace_id, agent_id, nodes_jsonl_path), ...] for all agents."""
    ws_root = data_dir / "workspaces"
    if not ws_root.exists():
        return []
    agents: List[Tuple[str, str, Path]] = []
    for ws_name in sorted(os.listdir(ws_root)):
        ws_path = ws_root / ws_name
        agents_root = ws_path / "agents"
        if not agents_root.exists():
            continue
        for agent_id in sorted(os.listdir(agents_root)):
            nodes_path = agents_root / agent_id / "private" / "nodes.jsonl"
            if nodes_path.exists():
                agents.append((ws_name, agent_id, nodes_path))
    return agents


# ---------------------------------------------------------------------------
# Guard re-verification per agent
# ---------------------------------------------------------------------------

def reverify_agent(
    workspace_id: str,
    agent_id: str,
    entities: Dict[int, Dict[str, Any]],
) -> Dict[str, Any]:
    """Run recursion_guard_check on every entity and return a report dict."""

    def lookup_fn(_ws: str, _ag: str, eid: int) -> Optional[Dict[str, Any]]:
        payload = entities.get(int(eid))
        if payload is None:
            return None
        return {"provenance": payload.get("provenance")}

    checked = 0
    admitted = 0
    rejected = 0
    no_provenance = 0
    failures: List[Dict[str, Any]] = []

    for eid, payload in sorted(entities.items()):
        if payload is None:
            # Tombstoned entity (quarantine --remove). Skip.
            continue
        checked += 1
        prov = payload.get("provenance") or {}

        # Classify expected guard behavior
        source_type = prov.get("source_type", "") if isinstance(prov, dict) else ""
        source_role = prov.get("source_role", "") if isinstance(prov, dict) else ""
        write_path = prov.get("write_path", "") if isinstance(prov, dict) else ""

        is_migration_refused = (
            prov.get("admission_refused") is True
            or source_type == SOURCE_GATE1_UNRECOVERABLE
        ) if isinstance(prov, dict) else False

        is_archivist_origin = (
            source_role == "archivist_writeback"
            or write_path == "cognition_writeback"
        )

        if not prov:
            no_provenance += 1

        ok, reason = recursion_guard_check(
            seed_eids=[eid],
            lookup_fn=lookup_fn,
            workspace_id=workspace_id,
            agent_id=agent_id,
        )

        if ok:
            admitted += 1
        else:
            rejected += 1

        # Detect unexpected outcomes
        if is_migration_refused and not (ok is False and reason == REASON_MIGRATION_REFUSED):
            failures.append({
                "eid": eid,
                "class": "migration_refused_not_rejected",
                "expected_reason": REASON_MIGRATION_REFUSED,
                "got_ok": ok,
                "got_reason": reason,
                "source_type": source_type,
            })
        elif is_archivist_origin and ok:
            # Archivist-origin entities should be rejected if they appear
            # as parents of other entities — but as seeds themselves, the
            # guard should reject them because their own provenance has
            # source_role=archivist_writeback (Rule A).
            failures.append({
                "eid": eid,
                "class": "archivist_origin_admitted",
                "got_ok": ok,
                "got_reason": reason,
                "source_role": source_role,
                "write_path": write_path,
            })

    return {
        "workspace_id": workspace_id,
        "agent_id": agent_id,
        "status": "PASS" if not failures else "FAIL",
        "checked": checked,
        "admitted": admitted,
        "rejected": rejected,
        "no_provenance": no_provenance,
        "failure_count": len(failures),
        "failures": failures,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Pre-gate-flip guard re-verification (D2 deliverable)")
    parser.add_argument(
        "--data-dir", type=str, default="data",
        help="Path to the TORMENT data directory (default: data/)")
    parser.add_argument(
        "--json", action="store_true",
        help="Emit full report as JSON instead of human-readable summary")
    args = parser.parse_args()

    data_dir = Path(args.data_dir).resolve()
    if not data_dir.exists():
        print(f"error: data directory not found: {data_dir}", file=sys.stderr)
        return 2

    agents = discover_agents(data_dir)
    if not agents:
        print(f"No workspaces/agents found under {data_dir}/workspaces/")
        return 0

    print(f"Guard re-verification — scanning {len(agents)} agent graph(s)\n")

    all_reports: List[Dict[str, Any]] = []
    any_failure = False

    for ws_id, ag_id, nodes_path in agents:
        print(f"  {ws_id}/{ag_id}: loading {nodes_path.name} ... ", end="", flush=True)
        entities = load_entities_from_jsonl(nodes_path)
        print(f"{len(entities)} entities")

        report = reverify_agent(ws_id, ag_id, entities)
        all_reports.append(report)

        status = report["status"]
        tag = "PASS" if status == "PASS" else "FAIL"
        print(f"    [{tag}] checked={report['checked']}  "
              f"admitted={report['admitted']}  rejected={report['rejected']}  "
              f"no_prov={report['no_provenance']}  failures={report['failure_count']}")

        if report["failures"]:
            any_failure = True
            for f in report["failures"]:
                print(f"      !! eid={f['eid']}  class={f['class']}  "
                      f"got_ok={f.get('got_ok')}  got_reason={f.get('got_reason')}")
        print()

    # Summary
    total_checked = sum(r["checked"] for r in all_reports)
    total_failures = sum(r["failure_count"] for r in all_reports)
    ws_pass = sum(1 for r in all_reports if r["status"] == "PASS")
    ws_fail = sum(1 for r in all_reports if r["status"] == "FAIL")

    print("=" * 60)
    print(f"SUMMARY: {len(all_reports)} agent(s), {total_checked} entities checked")
    print(f"  pass: {ws_pass}  fail: {ws_fail}  total failures: {total_failures}")
    print(f"  overall: {'PASS' if not any_failure else 'FAIL'}")

    if args.json:
        print("\n--- JSON report ---")
        print(json.dumps({
            "overall_status": "PASS" if not any_failure else "FAIL",
            "agents_checked": len(all_reports),
            "total_entities": total_checked,
            "total_failures": total_failures,
            "reports": all_reports,
        }, indent=2))

    return 0 if not any_failure else 1


if __name__ == "__main__":
    raise SystemExit(main())
