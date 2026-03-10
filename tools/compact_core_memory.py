#!/usr/bin/env python3
"""
compact_core_memory.py — TORMENT Phase 5 maintenance tool

Compacts core memory JSONL files by:
  1. Deduplicating nodes.jsonl (keep latest record per eid)
  2. Removing expired memories (half_life exhausted + strength below threshold)
  3. Writing compacted output atomically

This NEVER runs automatically during chat — it's an explicit maintenance action.

Usage:
    python -m tools.compact_core_memory --data-dir ./data --workspace default --agent ryuki
    python -m tools.compact_core_memory --data-dir ./data --workspace default --agent ryuki --dry-run
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

# Allow running from repo root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def _parse_jsonl(path: str):
    """Yield parsed JSON objects from a JSONL file, skipping bad lines."""
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def _write_jsonl(path: str, records):
    """Write records to JSONL atomically."""
    tmp = path + ".compact.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, default=str) + "\n")
    os.replace(tmp, path)


def _is_expired(node: dict, now_ts: float) -> bool:
    """Check if a node's half-life is exhausted and it should be compacted."""
    half_life_days = node.get("half_life_days") or node.get("payload", {}).get("half_life_days")
    if half_life_days is None:
        return False

    half_life_days = float(half_life_days)
    if half_life_days >= 365:  # Never expire long-lived memories (identity, canon)
        return False

    created_at = node.get("created_at") or node.get("payload", {}).get("created_at")
    if not created_at:
        # Check step-based age (rough heuristic)
        return False

    try:
        # Parse ISO timestamp
        import datetime
        if isinstance(created_at, str):
            ct = datetime.datetime.fromisoformat(created_at.replace("Z", "+00:00")).timestamp()
        else:
            ct = float(created_at)
    except Exception:
        return False

    age_days = (now_ts - ct) / 86400.0
    # A memory is "expired" if it's lived more than 5 half-lives
    # (< 3% of original strength remaining)
    if age_days > half_life_days * 5:
        # Also check strength/confidence — don't expire strong memories
        strength = float(node.get("strength") or node.get("payload", {}).get("strength", 0.5) or 0.5)
        if strength < 0.3:
            return True

    return False


def compact_nodes(nodes_path: str, dry_run: bool = False) -> dict:
    """Compact nodes.jsonl: deduplicate and remove expired entries."""
    now_ts = time.time()

    # Pass 1: load all records, keep latest per eid
    latest_by_eid: dict = {}
    total_records = 0

    for rec in _parse_jsonl(nodes_path):
        total_records += 1
        eid = rec.get("eid")
        if eid is not None:
            latest_by_eid[int(eid)] = rec  # later records overwrite earlier

    # Pass 2: filter expired
    kept = []
    expired_count = 0
    protected_kinds = {"seed", "identity", "canon_promotion"}

    for eid, node in sorted(latest_by_eid.items()):
        payload = node.get("payload", {})
        kind = payload.get("kind", "")
        tier = payload.get("tier", "")

        # Never compact seeds, identity anchors, or promoted canon
        if kind in protected_kinds or tier == "core_identity":
            kept.append(node)
            continue

        # Never compact canon-marked nodes
        if payload.get("canon", False):
            kept.append(node)
            continue

        if _is_expired(payload, now_ts):
            expired_count += 1
        else:
            kept.append(node)

    dedup_removed = total_records - len(latest_by_eid)
    stats = {
        "total_records": total_records,
        "unique_eids": len(latest_by_eid),
        "dedup_removed": dedup_removed,
        "expired_removed": expired_count,
        "kept": len(kept),
    }

    if not dry_run and (dedup_removed > 0 or expired_count > 0):
        # Backup original
        backup = nodes_path + f".bak.{int(time.time())}"
        try:
            os.rename(nodes_path, backup)
        except Exception:
            import shutil
            shutil.copy2(nodes_path, backup)
        _write_jsonl(nodes_path, kept)
        stats["backup"] = backup

    return stats


def compact_events(events_path: str, dry_run: bool = False) -> dict:
    """Compact events.jsonl: remove duplicate entries."""
    seen = set()
    records = []
    total = 0
    dupes = 0

    for rec in _parse_jsonl(events_path):
        total += 1
        # Create a dedup key from event content
        key = json.dumps(rec, sort_keys=True, default=str)
        if key in seen:
            dupes += 1
            continue
        seen.add(key)
        records.append(rec)

    stats = {"total_records": total, "duplicates_removed": dupes, "kept": len(records)}

    if not dry_run and dupes > 0:
        backup = events_path + f".bak.{int(time.time())}"
        try:
            os.rename(events_path, backup)
        except Exception:
            import shutil
            shutil.copy2(events_path, backup)
        _write_jsonl(events_path, records)
        stats["backup"] = backup

    return stats


def main():
    parser = argparse.ArgumentParser(description="Compact core memory JSONL files")
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--agent", required=True)
    parser.add_argument("--dry-run", action="store_true", help="Report stats without modifying files")
    args = parser.parse_args()

    private_dir = os.path.join(
        args.data_dir, "workspaces", args.workspace,
        "agents", args.agent, "private",
    )

    nodes_path = os.path.join(private_dir, "nodes.jsonl")
    events_path = os.path.join(private_dir, "memory_events.jsonl")

    print(f"{'[DRY RUN] ' if args.dry_run else ''}Compacting core memory for {args.workspace}/{args.agent}")
    print(f"  Private dir: {private_dir}")
    print()

    if os.path.exists(nodes_path):
        stats = compact_nodes(nodes_path, dry_run=args.dry_run)
        print("nodes.jsonl:")
        for k, v in stats.items():
            print(f"  {k}: {v}")
    else:
        print("nodes.jsonl: not found, skipping")

    print()

    if os.path.exists(events_path):
        stats = compact_events(events_path, dry_run=args.dry_run)
        print("memory_events.jsonl:")
        for k, v in stats.items():
            print(f"  {k}: {v}")
    else:
        print("memory_events.jsonl: not found, skipping")

    print("\nDone.")


if __name__ == "__main__":
    main()
