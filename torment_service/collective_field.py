# collective_field.py — Workspace-level collective resonance field
#
# Persists and queries ResonancePackets and ConvergenceEvents per workspace.
# This is the storage + retrieval layer for the hivemind — convergence
# detection will be added in Phase C.
#
# This module does NOT replace proposals or bridges. It sits above them.
# ---------------------------------------------------------------------------
from __future__ import annotations

import json
import os
import threading
import time
from typing import Any, Dict, List, Optional

from .collective_models import ResonancePacket, ConvergenceEvent


class CollectiveField:
    """Workspace-level collective resonance field.

    Stores packets (ingest snapshots) and events (convergence detections)
    as append-only JSONL files under the workspace data directory.

    Thread-safe for concurrent ingests within the same process.
    """

    def __init__(self, workspace_id: str, data_dir: str) -> None:
        self.workspace_id = workspace_id
        self._base = os.path.join(data_dir, "workspaces", workspace_id, "collective")
        os.makedirs(self._base, exist_ok=True)

        self._packets_path = os.path.join(self._base, "packets.jsonl")
        self._events_path = os.path.join(self._base, "events.jsonl")

        self._lock = threading.Lock()

        # Small in-memory cache for recent packets (convergence detection window)
        self._recent_packets: List[ResonancePacket] = []
        self._recent_max = 200  # keep last N in memory

        # Load existing packets into cache on startup
        self._warm_cache()

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------

    def _append_jsonl(self, path: str, obj: Dict[str, Any]) -> None:
        """Append one JSON line to a file (thread-safe)."""
        with self._lock:
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(obj, separators=(",", ":")) + "\n")

    def _read_jsonl(self, path: str) -> List[Dict[str, Any]]:
        """Read all JSON lines from a file."""
        if not os.path.exists(path):
            return []
        results = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        results.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return results

    def _warm_cache(self) -> None:
        """Load recent packets from disk into memory cache."""
        try:
            rows = self._read_jsonl(self._packets_path)
            # Keep only the last _recent_max
            recent = rows[-self._recent_max:] if len(rows) > self._recent_max else rows
            self._recent_packets = [ResonancePacket.from_dict(r) for r in recent]
        except Exception:
            self._recent_packets = []

    # ------------------------------------------------------------------
    # Packet operations
    # ------------------------------------------------------------------

    def append_packet(self, packet: ResonancePacket) -> None:
        """Persist a packet and add to in-memory cache."""
        self._append_jsonl(self._packets_path, packet.to_dict())
        with self._lock:
            self._recent_packets.append(packet)
            if len(self._recent_packets) > self._recent_max:
                self._recent_packets = self._recent_packets[-self._recent_max:]

    def recent_packets(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Return the most recent packets from cache."""
        with self._lock:
            pkts = self._recent_packets[-limit:]
        return [p.to_dict() for p in pkts]

    def packets_by_domain(self, domain_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Return recent packets filtered by domain."""
        with self._lock:
            filtered = [p for p in self._recent_packets if p.domain_id == domain_id]
        return [p.to_dict() for p in filtered[-limit:]]

    def packets_by_agent(self, agent_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Return recent packets filtered by agent."""
        with self._lock:
            filtered = [p for p in self._recent_packets if p.agent_id == agent_id]
        return [p.to_dict() for p in filtered[-limit:]]

    def all_packets(self, limit: int = 500) -> List[Dict[str, Any]]:
        """Read all packets from disk (not just cache). Expensive — use sparingly."""
        rows = self._read_jsonl(self._packets_path)
        return rows[-limit:]

    # ------------------------------------------------------------------
    # Event operations (convergence events — populated in Phase C)
    # ------------------------------------------------------------------

    def append_event(self, event: ConvergenceEvent) -> None:
        """Persist a convergence event."""
        self._append_jsonl(self._events_path, event.to_dict())

    def recent_events(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Return recent convergence events from disk."""
        rows = self._read_jsonl(self._events_path)
        return rows[-limit:]

    def events_by_domain(self, domain_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Return convergence events filtered by domain."""
        rows = self._read_jsonl(self._events_path)
        filtered = [r for r in rows if r.get("domain_id") == domain_id]
        return filtered[-limit:]

    def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Return a single convergence event by ID."""
        rows = self._read_jsonl(self._events_path)
        for r in rows:
            if r.get("event_id") == event_id:
                return r
        return None

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def status(self) -> Dict[str, Any]:
        """Return a summary of the collective field state."""
        with self._lock:
            cached = list(self._recent_packets)

        agents = set()
        domains = set()
        for p in cached:
            agents.add(p.agent_id)
            domains.add(p.domain_id)

        event_rows = self._read_jsonl(self._events_path)

        return {
            "workspace_id": self.workspace_id,
            "packet_count_cached": len(cached),
            "packet_count_total": self._count_lines(self._packets_path),
            "event_count": len(event_rows),
            "active_agents": sorted(agents),
            "active_domains": sorted(domains),
        }

    def _count_lines(self, path: str) -> int:
        """Count lines in a file without loading all data."""
        if not os.path.exists(path):
            return 0
        count = 0
        with open(path, "r", encoding="utf-8") as f:
            for _ in f:
                count += 1
        return count
