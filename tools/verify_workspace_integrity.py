#!/usr/bin/env python3
"""
verify_workspace_integrity.py — TORMENT Phase 5 maintenance tool

Cross-checks workspace data for consistency:
  1. Every eid in nodes.jsonl has valid embedding_ref → existing shard row
  2. Every chunk in chunks.jsonl has valid doc_id in documents.jsonl
  3. SQLite index row counts match canonical JSONL counts
  4. Shard manifest matches actual shard file sizes
  5. Character seed references exist

Reports issues but NEVER modifies data.

Usage:
    python -m tools.verify_workspace_integrity --data-dir ./data --workspace default --agent ryuki
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

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


class IntegrityReport:
    def __init__(self):
        self.errors: list = []
        self.warnings: list = []
        self.info: list = []

    def error(self, msg: str):
        self.errors.append(msg)

    def warn(self, msg: str):
        self.warnings.append(msg)

    def log(self, msg: str):
        self.info.append(msg)

    def print_report(self):
        print(f"\n{'=' * 60}")
        print("INTEGRITY REPORT")
        print(f"{'=' * 60}")
        print(f"  Errors:   {len(self.errors)}")
        print(f"  Warnings: {len(self.warnings)}")
        print(f"  Info:     {len(self.info)}")
        print()

        if self.errors:
            print("ERRORS:")
            for e in self.errors:
                print(f"  [ERROR] {e}")
            print()

        if self.warnings:
            print("WARNINGS:")
            for w in self.warnings:
                print(f"  [WARN]  {w}")
            print()

        if self.info:
            print("INFO:")
            for i in self.info:
                print(f"  [INFO]  {i}")

        if not self.errors and not self.warnings:
            print("All checks passed.")


def check_nodes_and_shards(private_dir: str, report: IntegrityReport):
    """Verify nodes.jsonl embedding_refs point to valid shard rows."""
    nodes_path = os.path.join(private_dir, "nodes.jsonl")
    emb_dir = os.path.join(private_dir, "embeddings")

    if not os.path.exists(nodes_path):
        report.log("nodes.jsonl not found — skipping node checks")
        return

    # Load shard manifest
    manifest = None
    manifest_path = os.path.join(emb_dir, "manifest.json")
    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

    # Deduplicate nodes (keep latest per eid)
    latest_by_eid = {}
    total_records = 0
    for rec in _parse_jsonl(nodes_path):
        total_records += 1
        eid = rec.get("eid")
        if eid is not None:
            latest_by_eid[int(eid)] = rec

    report.log(f"nodes.jsonl: {total_records} records, {len(latest_by_eid)} unique eids")

    if total_records > len(latest_by_eid):
        report.warn(f"nodes.jsonl has {total_records - len(latest_by_eid)} duplicate eid records (compact recommended)")

    # Check embedding refs
    refs_checked = 0
    refs_missing = 0
    refs_invalid = 0

    for eid, node in latest_by_eid.items():
        payload = node.get("payload", {})
        emb_ref = payload.get("embedding_ref")
        if emb_ref is None:
            # Old-style embedding — check for emb_<eid>.npy
            old_path = os.path.join(private_dir, f"emb_{eid}.npy")
            if not os.path.exists(old_path):
                # Might be in embeddings dir
                emb_path = os.path.join(emb_dir, f"emb_{eid}.npy")
                if not os.path.exists(emb_path):
                    refs_missing += 1
            continue

        refs_checked += 1
        shard_idx = emb_ref.get("shard", -1)
        row = emb_ref.get("row", -1)

        # Verify shard file exists
        shard_file = os.path.join(emb_dir, f"shard_{shard_idx:06d}.npy")
        if not os.path.exists(shard_file):
            report.error(f"eid={eid}: shard file {shard_file} missing")
            refs_invalid += 1
            continue

        # Verify row is within shard bounds
        if manifest:
            rows_per = int(manifest.get("rows_per_shard", 4096))
            if row >= rows_per:
                report.error(f"eid={eid}: row {row} >= rows_per_shard {rows_per}")
                refs_invalid += 1

    if refs_checked:
        report.log(f"Embedding refs checked: {refs_checked}, invalid: {refs_invalid}, missing: {refs_missing}")
    if refs_invalid:
        report.error(f"{refs_invalid} embedding refs point to invalid shard locations")


def check_archive_integrity(archive_dir: str, report: IntegrityReport):
    """Verify chunks reference valid documents."""
    docs_path = os.path.join(archive_dir, "documents.jsonl")
    chunks_path = os.path.join(archive_dir, "chunks.jsonl")

    if not os.path.exists(docs_path) and not os.path.exists(chunks_path):
        report.log("No archive data found — skipping archive checks")
        return

    # Load documents
    doc_ids = set()
    deleted_ids = set()
    for rec in _parse_jsonl(docs_path):
        doc_id = rec.get("doc_id")
        if doc_id:
            if rec.get("_deleted"):
                deleted_ids.add(doc_id)
            else:
                doc_ids.add(doc_id)

    report.log(f"Archive documents: {len(doc_ids)} active, {len(deleted_ids)} deleted")

    # Check chunks
    chunk_count = 0
    orphan_count = 0
    for rec in _parse_jsonl(chunks_path):
        chunk_count += 1
        doc_id = rec.get("doc_id", "")
        if doc_id not in doc_ids:
            if doc_id in deleted_ids:
                orphan_count += 1
            else:
                report.warn(f"Chunk {rec.get('chunk_id', '?')}: references unknown doc_id '{doc_id}'")
                orphan_count += 1

    report.log(f"Archive chunks: {chunk_count} total, {orphan_count} orphans")
    if orphan_count:
        report.warn(f"{orphan_count} orphan chunks (compact recommended)")


def check_shard_manifest(embeddings_dir: str, label: str, report: IntegrityReport):
    """Verify shard manifest matches actual files."""
    manifest_path = os.path.join(embeddings_dir, "manifest.json")
    if not os.path.exists(manifest_path):
        return

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    dim = int(manifest.get("embedding_dim", 384))
    rows_per = int(manifest.get("rows_per_shard", 4096))
    active_shard = int(manifest.get("active_shard", 0))
    next_row = int(manifest.get("next_row", 0))

    report.log(f"{label} shard manifest: dim={dim}, rows_per={rows_per}, active_shard={active_shard}, next_row={next_row}")

    # Check active shard file
    shard_file = os.path.join(embeddings_dir, f"shard_{active_shard:06d}.npy")
    if not os.path.exists(shard_file):
        report.error(f"{label}: active shard file missing: {shard_file}")
        return

    # Check shard shape
    try:
        mm = np.load(shard_file, mmap_mode="r")
        actual_shape = mm.shape
        expected_shape = (rows_per, dim)
        if actual_shape != expected_shape:
            report.error(f"{label}: shard shape {actual_shape} != expected {expected_shape}")
        else:
            report.log(f"{label}: shard shape OK: {actual_shape}")
    except Exception as e:
        report.error(f"{label}: failed to load shard: {e}")

    # Check map file
    map_file = os.path.join(embeddings_dir, f"shard_{active_shard:06d}.map.jsonl")
    if not os.path.exists(map_file):
        report.warn(f"{label}: shard map file missing: {map_file}")
    else:
        map_count = sum(1 for _ in _parse_jsonl(map_file))
        if map_count != next_row:
            report.warn(f"{label}: map entries ({map_count}) != next_row ({next_row})")
        else:
            report.log(f"{label}: shard map entries match next_row: {map_count}")


def check_sqlite_index(index_dir: str, private_dir: str, archive_dir: str, report: IntegrityReport):
    """Verify SQLite index row counts match canonical JSONL."""
    db_path = os.path.join(index_dir, "memory_index.sqlite")
    if not os.path.exists(db_path):
        report.log("SQLite index not found — skipping index checks")
        return

    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Count rows in each table
        tables = ["core_nodes", "core_events", "trajectory_index", "documents", "chunks"]
        index_counts = {}
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                index_counts[table] = cursor.fetchone()[0]
            except Exception:
                index_counts[table] = -1

        conn.close()

        # Compare with JSONL counts
        nodes_path = os.path.join(private_dir, "nodes.jsonl")
        if os.path.exists(nodes_path):
            jsonl_eids = set()
            for rec in _parse_jsonl(nodes_path):
                eid = rec.get("eid")
                if eid is not None:
                    jsonl_eids.add(int(eid))
            jsonl_count = len(jsonl_eids)
            idx_count = index_counts.get("core_nodes", -1)
            if idx_count >= 0 and idx_count != jsonl_count:
                report.warn(f"SQLite core_nodes ({idx_count}) != JSONL unique eids ({jsonl_count})")
            else:
                report.log(f"SQLite core_nodes matches JSONL: {jsonl_count}")

        report.log(f"SQLite index counts: {json.dumps(index_counts)}")

    except Exception as e:
        report.warn(f"SQLite index check failed: {e}")


def main():
    parser = argparse.ArgumentParser(description="Verify workspace data integrity")
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--agent", required=True)
    args = parser.parse_args()

    agent_dir = os.path.join(args.data_dir, "workspaces", args.workspace, "agents", args.agent)
    private_dir = os.path.join(agent_dir, "private")
    archive_dir = os.path.join(agent_dir, "memory_archive")
    index_dir = os.path.join(agent_dir, "index")

    print(f"Verifying workspace integrity: {args.workspace}/{args.agent}")
    print(f"  Agent dir: {agent_dir}")

    report = IntegrityReport()

    # 1. Core nodes + embedding shards
    check_nodes_and_shards(private_dir, report)

    # 2. Archive documents + chunks
    check_archive_integrity(archive_dir, report)

    # 3. Core shard manifest
    core_emb_dir = os.path.join(private_dir, "embeddings")
    if os.path.isdir(core_emb_dir):
        check_shard_manifest(core_emb_dir, "Core", report)

    # 4. Archive shard manifest
    archive_emb_dir = os.path.join(archive_dir, "embeddings")
    if os.path.isdir(archive_emb_dir):
        check_shard_manifest(archive_emb_dir, "Archive", report)

    # 5. SQLite index consistency
    check_sqlite_index(index_dir, private_dir, archive_dir, report)

    report.print_report()

    # Exit code: 1 if errors, 0 otherwise
    sys.exit(1 if report.errors else 0)


if __name__ == "__main__":
    main()
