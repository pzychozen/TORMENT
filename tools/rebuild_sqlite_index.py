#!/usr/bin/env python3
"""
Rebuild SQLite sidecar index from canonical JSONL sources.

Usage:
    python tools/rebuild_sqlite_index.py --data-dir ./data
    python tools/rebuild_sqlite_index.py --data-dir ./data --workspace ryuki --agent ryuki_nox
    python tools/rebuild_sqlite_index.py --data-dir ./data --dry-run

This is safe to run at any time. The SQLite index is a disposable cache
that can always be rebuilt from the canonical JSONL/NPY files.
"""
from __future__ import annotations

import argparse
import os
import sys
import time

# Allow running from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.sqlite_index import IndexManager


def find_agents(data_dir: str, workspace_filter: str = "", agent_filter: str = ""):
    """Find all workspace/agent pairs under the data directory."""
    ws_root = os.path.join(data_dir, "workspaces")
    if not os.path.isdir(ws_root):
        print(f"No workspaces directory found at {ws_root}")
        return []

    agents = []
    for ws_id in sorted(os.listdir(ws_root)):
        if workspace_filter and ws_id != workspace_filter:
            continue
        agents_dir = os.path.join(ws_root, ws_id, "agents")
        if not os.path.isdir(agents_dir):
            continue
        for agent_id in sorted(os.listdir(agents_dir)):
            if agent_filter and agent_id != agent_filter:
                continue
            agents.append((ws_id, agent_id))

    return agents


def rebuild_agent_index(
    data_dir: str,
    workspace_id: str,
    agent_id: str,
    dry_run: bool = False,
) -> dict:
    """Rebuild the SQLite index for a single agent."""
    agent_dir = os.path.join(data_dir, "workspaces", workspace_id, "agents", agent_id)
    private_dir = os.path.join(agent_dir, "private")
    archive_dir = os.path.join(agent_dir, "memory_archive")
    index_dir = os.path.join(agent_dir, "index")

    # Check what source files exist
    sources = {
        "nodes.jsonl": os.path.join(private_dir, "nodes.jsonl"),
        "memory_events.jsonl": os.path.join(private_dir, "memory_events.jsonl"),
        "trajectories.jsonl": os.path.join(private_dir, "trajectories.jsonl"),
        "documents.jsonl": os.path.join(archive_dir, "documents.jsonl"),
        "chunks.jsonl": os.path.join(archive_dir, "chunks.jsonl"),
    }

    existing_sources = {k: v for k, v in sources.items() if os.path.exists(v)}

    if not existing_sources:
        return {"status": "skipped", "reason": "no source files found"}

    if dry_run:
        return {
            "status": "dry_run",
            "sources_found": list(existing_sources.keys()),
            "index_dir": index_dir,
        }

    # Create index manager and rebuild
    idx = IndexManager(index_dir)
    if not idx.available:
        return {"status": "error", "reason": "could not create SQLite database"}

    # Find motifs file (JSON, not JSONL)
    motifs_files = []
    domains_dir = os.path.join(data_dir, "workspaces", workspace_id, "domains")
    if os.path.isdir(domains_dir):
        for domain_id in os.listdir(domains_dir):
            mpath = os.path.join(domains_dir, domain_id, "motifs.json")
            if os.path.exists(mpath):
                motifs_files.append(mpath)

    counts = idx.rebuild_from_jsonl(
        nodes_path=sources.get("nodes.jsonl", ""),
        events_path=sources.get("memory_events.jsonl", ""),
        trajectories_path=sources.get("trajectories.jsonl", ""),
        archive_documents_path=sources.get("documents.jsonl", ""),
        archive_chunks_path=sources.get("chunks.jsonl", ""),
        motifs_path=motifs_files[0] if motifs_files else "",
    )

    idx.close()

    return {
        "status": "rebuilt",
        "index_path": idx.db_path,
        "counts": counts,
    }


def main():
    parser = argparse.ArgumentParser(description="Rebuild SQLite sidecar index")
    parser.add_argument("--data-dir", required=True, help="Path to TORMENT data directory")
    parser.add_argument("--workspace", default="", help="Filter to specific workspace")
    parser.add_argument("--agent", default="", help="Filter to specific agent")
    parser.add_argument("--dry-run", action="store_true", help="Preview without rebuilding")
    args = parser.parse_args()

    data_dir = os.path.abspath(args.data_dir)
    if not os.path.isdir(data_dir):
        print(f"Error: data directory not found: {data_dir}")
        sys.exit(1)

    agents = find_agents(data_dir, args.workspace, args.agent)
    if not agents:
        print("No agents found to rebuild.")
        sys.exit(0)

    print(f"Found {len(agents)} agent(s) to process")
    if args.dry_run:
        print("(DRY RUN — no changes will be made)\n")

    total_ok = 0
    total_skip = 0
    total_err = 0

    for ws_id, agent_id in agents:
        print(f"\n--- {ws_id}/{agent_id} ---")
        t0 = time.time()
        result = rebuild_agent_index(data_dir, ws_id, agent_id, dry_run=args.dry_run)
        elapsed = time.time() - t0

        status = result.get("status", "unknown")
        if status == "rebuilt":
            counts = result.get("counts", {})
            total_ok += 1
            print(f"  Rebuilt in {elapsed:.2f}s")
            for table, count in counts.items():
                print(f"    {table}: {count} rows")
        elif status == "dry_run":
            total_ok += 1
            print(f"  Sources found: {', '.join(result.get('sources_found', []))}")
            print(f"  Would write to: {result.get('index_dir')}")
        elif status == "skipped":
            total_skip += 1
            print(f"  Skipped: {result.get('reason')}")
        else:
            total_err += 1
            print(f"  Error: {result.get('reason')}")

    print(f"\n{'='*40}")
    print(f"Done: {total_ok} rebuilt, {total_skip} skipped, {total_err} errors")


if __name__ == "__main__":
    main()
