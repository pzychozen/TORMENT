#!/usr/bin/env python3
"""
compact_archive_memory.py — TORMENT Phase 5 maintenance tool

Compacts archive memory by:
  1. Removing orphan chunks (chunk references a deleted doc_id)
  2. Deduplicating documents.jsonl and chunks.jsonl
  3. Writing compacted output atomically

This NEVER runs automatically during chat — it's an explicit maintenance action.

Usage:
    python -m tools.compact_archive_memory --data-dir ./data --workspace default --agent ryuki
    python -m tools.compact_archive_memory --data-dir ./data --workspace default --agent ryuki --dry-run
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def _parse_jsonl(path: str):
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
    tmp = path + ".compact.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, default=str) + "\n")
    os.replace(tmp, path)


def compact_documents(docs_path: str, dry_run: bool = False) -> dict:
    """Deduplicate documents.jsonl — keep latest record per doc_id."""
    latest_by_id: dict = {}
    total = 0

    for rec in _parse_jsonl(docs_path):
        total += 1
        doc_id = rec.get("doc_id")
        if doc_id:
            latest_by_id[doc_id] = rec

    # Filter out deleted documents (marked with _deleted flag)
    active = {k: v for k, v in latest_by_id.items() if not v.get("_deleted", False)}
    deleted_count = len(latest_by_id) - len(active)
    dedup_removed = total - len(latest_by_id)

    stats = {
        "total_records": total,
        "unique_docs": len(latest_by_id),
        "dedup_removed": dedup_removed,
        "deleted_docs": deleted_count,
        "active_docs": len(active),
    }

    if not dry_run and (dedup_removed > 0 or deleted_count > 0):
        backup = docs_path + f".bak.{int(time.time())}"
        try:
            os.rename(docs_path, backup)
        except Exception:
            import shutil
            shutil.copy2(docs_path, backup)
        _write_jsonl(docs_path, active.values())
        stats["backup"] = backup

    return stats, set(active.keys())


def compact_chunks(chunks_path: str, active_doc_ids: set, dry_run: bool = False) -> dict:
    """Compact chunks.jsonl — deduplicate and remove orphans."""
    latest_by_id: dict = {}
    total = 0

    for rec in _parse_jsonl(chunks_path):
        total += 1
        chunk_id = rec.get("chunk_id")
        if chunk_id:
            latest_by_id[chunk_id] = rec

    # Remove orphan chunks (doc_id not in active documents)
    kept = {}
    orphan_count = 0
    for chunk_id, rec in latest_by_id.items():
        doc_id = rec.get("doc_id", "")
        if doc_id in active_doc_ids:
            kept[chunk_id] = rec
        else:
            orphan_count += 1

    dedup_removed = total - len(latest_by_id)

    stats = {
        "total_records": total,
        "unique_chunks": len(latest_by_id),
        "dedup_removed": dedup_removed,
        "orphans_removed": orphan_count,
        "kept": len(kept),
    }

    if not dry_run and (dedup_removed > 0 or orphan_count > 0):
        backup = chunks_path + f".bak.{int(time.time())}"
        try:
            os.rename(chunks_path, backup)
        except Exception:
            import shutil
            shutil.copy2(chunks_path, backup)
        _write_jsonl(chunks_path, kept.values())
        stats["backup"] = backup

    return stats


def main():
    parser = argparse.ArgumentParser(description="Compact archive memory JSONL files")
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--agent", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    archive_dir = os.path.join(
        args.data_dir, "workspaces", args.workspace,
        "agents", args.agent, "memory_archive",
    )

    docs_path = os.path.join(archive_dir, "documents.jsonl")
    chunks_path = os.path.join(archive_dir, "chunks.jsonl")

    print(f"{'[DRY RUN] ' if args.dry_run else ''}Compacting archive memory for {args.workspace}/{args.agent}")
    print(f"  Archive dir: {archive_dir}")
    print()

    active_doc_ids = set()

    if os.path.exists(docs_path):
        stats, active_doc_ids = compact_documents(docs_path, dry_run=args.dry_run)
        print("documents.jsonl:")
        for k, v in stats.items():
            print(f"  {k}: {v}")
    else:
        print("documents.jsonl: not found, skipping")

    print()

    if os.path.exists(chunks_path):
        stats = compact_chunks(chunks_path, active_doc_ids, dry_run=args.dry_run)
        print("chunks.jsonl:")
        for k, v in stats.items():
            print(f"  {k}: {v}")
    else:
        print("chunks.jsonl: not found, skipping")

    print("\nDone.")


if __name__ == "__main__":
    main()
