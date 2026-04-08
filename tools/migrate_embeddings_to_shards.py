#!/usr/bin/env python3
"""
Migrate legacy per-file embeddings (emb_<eid>.npy) to shard storage.

Usage:
    python -m tools.migrate_embeddings_to_shards --data-dir ./data

Or from the project root:
    python tools/migrate_embeddings_to_shards.py --data-dir ./data

This script:
  1. Scans all graph directories for emb_*.npy files
  2. Writes each embedding into shard storage (embeddings/ subfolder)
  3. Updates nodes.jsonl with embedding_ref and memory_class fields
  4. Moves old emb_*.npy files to legacy_embeddings/ (does NOT delete)
  5. Generates a migration report

Safe to run multiple times — already-migrated nodes are skipped.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from typing import Any, Dict, List, Tuple

import numpy as np

# Allow running from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from torment_service.embedding_store import EmbeddingShardWriter


def _find_graph_dirs(data_dir: str) -> List[str]:
    """Find all directories containing nodes.jsonl (graph directories)."""
    results = []
    for root, dirs, files in os.walk(data_dir):
        if "nodes.jsonl" in files:
            results.append(root)
    return results


def _load_nodes(nodes_path: str) -> Dict[int, Dict[str, Any]]:
    """Load nodes.jsonl, keeping last record per EID as canonical."""
    nodes: Dict[int, Dict[str, Any]] = {}
    if not os.path.exists(nodes_path):
        return nodes
    with open(nodes_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
                eid = int(obj.get("eid", 0))
                nodes[eid] = obj
            except (json.JSONDecodeError, ValueError):
                continue
    return nodes


def _find_legacy_embeddings(graph_dir: str) -> List[Tuple[int, str]]:
    """Find all emb_<eid>.npy files and return (eid, path) pairs."""
    results = []
    for fn in os.listdir(graph_dir):
        if fn.startswith("emb_") and fn.endswith(".npy"):
            try:
                eid = int(fn[4:-4])  # emb_123.npy → 123
                results.append((eid, os.path.join(graph_dir, fn)))
            except ValueError:
                continue
    return sorted(results, key=lambda t: t[0])


def migrate_graph(graph_dir: str, dry_run: bool = False) -> Dict[str, Any]:
    """Migrate one graph directory from per-file to shard storage.

    Returns a report dict with counts.
    """
    report = {
        "graph_dir": graph_dir,
        "legacy_found": 0,
        "already_migrated": 0,
        "migrated": 0,
        "errors": 0,
        "nodes_updated": 0,
    }

    nodes_path = os.path.join(graph_dir, "nodes.jsonl")
    legacy_embs = _find_legacy_embeddings(graph_dir)
    report["legacy_found"] = len(legacy_embs)

    if not legacy_embs:
        return report

    # Load current nodes
    nodes = _load_nodes(nodes_path)

    # Check which are already migrated
    to_migrate: List[Tuple[int, str]] = []
    for eid, emb_path in legacy_embs:
        node = nodes.get(eid)
        if node:
            payload = node.get("payload", {}) or {}
            if payload.get("embedding_ref"):
                report["already_migrated"] += 1
                continue
        to_migrate.append((eid, emb_path))

    if not to_migrate:
        return report

    if dry_run:
        report["migrated"] = len(to_migrate)
        return report

    # Create shard writer
    emb_dir = os.path.join(graph_dir, "embeddings")
    # Detect embedding dim from first file
    first_emb = np.load(to_migrate[0][1])
    dim = int(first_emb.reshape(-1).shape[0])
    writer = EmbeddingShardWriter(emb_dir, dim=dim)

    # Legacy archive directory
    legacy_dir = os.path.join(graph_dir, "legacy_embeddings")
    os.makedirs(legacy_dir, exist_ok=True)

    # Migrate each embedding
    for eid, emb_path in to_migrate:
        try:
            vec = np.load(emb_path).astype(np.float32).reshape(-1)

            # Determine memory_class and kind from node payload
            node = nodes.get(eid, {})
            payload = node.get("payload", {}) or {}
            memory_class = str(payload.get("memory_class", "core"))
            kind = str(payload.get("type", "episode"))
            step = int(payload.get("created_at", 0) or 0)

            emb_ref = writer.append(
                vec,
                eid=eid,
                memory_class=memory_class,
                kind=kind,
                step=step,
            )

            # Update node payload with embedding_ref and memory_class
            if eid in nodes:
                if "payload" not in nodes[eid]:
                    nodes[eid]["payload"] = {}
                nodes[eid]["payload"]["embedding_ref"] = emb_ref
                if "memory_class" not in nodes[eid]["payload"]:
                    nodes[eid]["payload"]["memory_class"] = "core"

            # Move old file to legacy
            legacy_path = os.path.join(legacy_dir, os.path.basename(emb_path))
            shutil.move(emb_path, legacy_path)

            report["migrated"] += 1

        except Exception as e:
            print(f"  ERROR migrating eid={eid}: {e}")
            report["errors"] += 1

    # Rewrite nodes.jsonl with updated payloads
    if report["migrated"] > 0:
        # Write to temp then replace
        tmp_path = nodes_path + ".migrating"
        with open(tmp_path, "w", encoding="utf-8") as f:
            for eid in sorted(nodes.keys()):
                f.write(json.dumps(nodes[eid], ensure_ascii=False) + "\n")
        os.replace(tmp_path, nodes_path)
        report["nodes_updated"] = len(nodes)

    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate emb_*.npy to shard storage")
    parser.add_argument("--data-dir", required=True, help="Root data directory")
    parser.add_argument("--dry-run", action="store_true", help="Report only, don't change files")
    args = parser.parse_args()

    data_dir = os.path.abspath(args.data_dir)
    if not os.path.isdir(data_dir):
        print(f"ERROR: Data directory not found: {data_dir}")
        sys.exit(1)

    print(f"Scanning {data_dir} for graph directories...")
    graph_dirs = _find_graph_dirs(data_dir)
    print(f"Found {len(graph_dirs)} graph directories")

    if args.dry_run:
        print("DRY RUN — no files will be changed\n")

    total = {
        "graphs": len(graph_dirs),
        "legacy_found": 0,
        "already_migrated": 0,
        "migrated": 0,
        "errors": 0,
        "nodes_updated": 0,
    }

    for i, gdir in enumerate(graph_dirs, 1):
        rel = os.path.relpath(gdir, data_dir)
        print(f"\n[{i}/{len(graph_dirs)}] {rel}")
        report = migrate_graph(gdir, dry_run=args.dry_run)
        for k in total:
            if k != "graphs":
                total[k] += report.get(k, 0)
        if report["legacy_found"]:
            print(f"  legacy: {report['legacy_found']}, "
                  f"already migrated: {report['already_migrated']}, "
                  f"migrated: {report['migrated']}, "
                  f"errors: {report['errors']}")
        else:
            print(f"  no legacy embeddings found")

    print(f"\n{'='*50}")
    print(f"Migration {'(DRY RUN) ' if args.dry_run else ''}complete:")
    print(f"  Graphs scanned:     {total['graphs']}")
    print(f"  Legacy files found: {total['legacy_found']}")
    print(f"  Already migrated:   {total['already_migrated']}")
    print(f"  Newly migrated:     {total['migrated']}")
    print(f"  Errors:             {total['errors']}")
    print(f"  Nodes updated:      {total['nodes_updated']}")

    if total["errors"] > 0:
        print("\nWARNING: Some embeddings failed to migrate. Check output above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
