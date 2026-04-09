# collective_field.py — Workspace-level collective resonance field
#
# Persists and queries ResonancePackets and ConvergenceEvents per workspace.
# This is the storage + retrieval layer for the hivemind. Convergence
# detection runs on ingest, comparing the new packet against recent packets
# from OTHER agents in the same domain.
#
# This module does NOT replace proposals or bridges. It sits above them.
# ---------------------------------------------------------------------------
from __future__ import annotations

import json
import logging
import os
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .collective_models import ResonancePacket, ConvergenceEvent
from .embedding_store import _canonical_storage_root, _child_path
from .pathing import safe_slug

log = logging.getLogger("torment.collective_field")


class CollectiveField:
    """Workspace-level collective resonance field.

    Stores packets (ingest snapshots) and events (convergence detections)
    as append-only JSONL files under the workspace data directory.

    Thread-safe for concurrent ingests within the same process.
    """

    # Convergence detection defaults
    CONVERGENCE_SIM_THRESHOLD = 0.72     # cosine similarity to trigger
    CONVERGENCE_TIME_WINDOW = 100        # max age difference in steps
    CONVERGENCE_MIN_AGENTS = 2           # minimum distinct agents
    CONVERGENCE_COOLDOWN = 30            # seconds between events for same agent pair + domain

    def __init__(self, workspace_id: str, data_dir: str) -> None:
        self.workspace_id = safe_slug(workspace_id, "workspace_id")

        # Canonical trust chain: data_dir → workspaces/<id>/collective
        canonical_data = _canonical_storage_root(data_dir)
        ws_dir = os.path.realpath(os.path.join(canonical_data, "workspaces", self.workspace_id, "collective"))
        if not ws_dir.startswith(canonical_data + os.sep):
            raise ValueError(f"Workspace path escapes base: {ws_dir!r}")
        os.makedirs(ws_dir, exist_ok=True)
        self._base = ws_dir
        self._packets_path = _child_path(ws_dir, "packets.jsonl")
        self._events_path = _child_path(ws_dir, "events.jsonl")

        self._lock = threading.Lock()

        # Small in-memory cache for recent packets (convergence detection window)
        self._recent_packets: List[ResonancePacket] = []
        self._recent_embeddings: Dict[str, np.ndarray] = {}  # packet_id -> embedding (in-memory only)
        self._recent_max = 200  # keep last N in memory

        # Deduplication: track recent convergence events to avoid spam
        # key: frozenset({agent1, agent2}) + domain -> last event timestamp
        self._event_cooldowns: Dict[str, int] = {}

        # Load existing packets into cache on startup
        self._warm_cache()

    def _guard(self, path: str) -> str:
        """Guard a path to ensure it doesn't escape the workspace root."""
        rp = os.path.realpath(path)
        base = os.path.realpath(self._base)
        if rp != base and not rp.startswith(base + os.sep):
            raise ValueError(f"Path escapes workspace root: {rp!r}")
        return rp

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------

    def _append_jsonl(self, path: str, obj: Dict[str, Any]) -> None:
        """Append one JSON line to a file (thread-safe)."""
        with self._lock:
            with open(self._guard(path), "a", encoding="utf-8") as f:
                f.write(json.dumps(obj, separators=(",", ":")) + "\n")

    def _read_jsonl(self, path: str) -> List[Dict[str, Any]]:
        """Read all JSON lines from a file."""
        guarded_path = self._guard(path)
        if not os.path.exists(guarded_path):
            return []
        results = []
        with open(guarded_path, "r", encoding="utf-8") as f:
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

    def append_packet(
        self,
        packet: ResonancePacket,
        embedding: Optional[np.ndarray] = None,
    ) -> Optional[ConvergenceEvent]:
        """Persist a packet, add to cache, and run convergence detection.

        Args:
            packet: The resonance packet to store.
            embedding: Optional full embedding vector for similarity computation.
                       Kept in-memory only — not written to JSONL.

        Returns:
            A ConvergenceEvent if convergence was detected, else None.
        """
        self._append_jsonl(self._packets_path, packet.to_dict())
        with self._lock:
            self._recent_packets.append(packet)
            if embedding is not None:
                self._recent_embeddings[packet.packet_id] = np.asarray(embedding, dtype=np.float32)
            if len(self._recent_packets) > self._recent_max:
                # Evict oldest
                evicted = self._recent_packets[:-self._recent_max]
                self._recent_packets = self._recent_packets[-self._recent_max:]
                for ep in evicted:
                    self._recent_embeddings.pop(ep.packet_id, None)

        # Convergence detection (only if we have an embedding)
        if embedding is not None:
            return self.detect_convergence(packet, embedding)
        return None

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

    # ------------------------------------------------------------------
    # Convergence detection
    # ------------------------------------------------------------------

    def detect_convergence(
        self,
        new_packet: ResonancePacket,
        new_embedding: np.ndarray,
    ) -> Optional[ConvergenceEvent]:
        """Check if a new packet converges with recent packets from other agents.

        Convergence requires:
            1. Same workspace + same domain
            2. Different agent
            3. Semantic similarity >= threshold
            4. Not in cooldown (same agent-pair + domain)

        Bonuses for phase/symbol/motif alignment increase confidence.

        Returns a ConvergenceEvent if detected, else None.
        """
        new_emb_norm = np.linalg.norm(new_embedding)
        if new_emb_norm < 1e-12:
            return None
        new_unit = new_embedding / new_emb_norm

        now_ts = int(time.time())
        best_match: Optional[Tuple[ResonancePacket, float]] = None
        best_sim = 0.0

        with self._lock:
            candidates = list(self._recent_packets)
            emb_cache = dict(self._recent_embeddings)

        for pkt in candidates:
            # Must be same domain, different agent
            if pkt.domain_id != new_packet.domain_id:
                continue
            if pkt.agent_id == new_packet.agent_id:
                continue

            # Check embedding similarity
            other_emb = emb_cache.get(pkt.packet_id)
            if other_emb is None:
                continue
            other_norm = np.linalg.norm(other_emb)
            if other_norm < 1e-12:
                continue
            sim = float(np.dot(new_unit, other_emb / other_norm))

            if sim >= self.CONVERGENCE_SIM_THRESHOLD and sim > best_sim:
                best_sim = sim
                best_match = (pkt, sim)

        if best_match is None:
            return None

        other_pkt, semantic_sim = best_match

        # Cooldown check: don't fire for same agent pair + domain within window
        pair_key = self._pair_key(new_packet.agent_id, other_pkt.agent_id, new_packet.domain_id)
        last_event_ts = self._event_cooldowns.get(pair_key, 0)
        if (now_ts - last_event_ts) < self.CONVERGENCE_COOLDOWN:
            return None

        # Compute alignment bonuses
        phase_align = self._phase_alignment(new_packet, other_pkt)
        symbol_align = self._symbol_alignment(new_packet, other_pkt)
        motif_align = self._motif_alignment(new_packet, other_pkt)

        # Composite confidence: weighted combination
        confidence = (
            0.50 * semantic_sim +
            0.15 * phase_align +
            0.15 * symbol_align +
            0.20 * motif_align
        )

        # Must clear minimum composite threshold
        if confidence < 0.45:
            return None

        # Build the event
        event = ConvergenceEvent(
            workspace_id=self.workspace_id,
            domain_id=new_packet.domain_id,
            ts_start=min(new_packet.ts, other_pkt.ts),
            ts_end=max(new_packet.ts, other_pkt.ts),
            participating_agents=sorted([new_packet.agent_id, other_pkt.agent_id]),
            source_packets=[other_pkt.packet_id, new_packet.packet_id],
            source_eids=[
                e for e in [other_pkt.source_eid, new_packet.source_eid] if e is not None
            ],
            confidence=round(confidence, 4),
            persistence=0.0,  # will be meaningful once temporal tracking exists
            semantic_overlap=round(semantic_sim, 4),
            phase_alignment=round(phase_align, 4),
            symbol_alignment=round(symbol_align, 4),
            dominant_motifs=self._shared_motifs(new_packet, other_pkt),
            dominant_symbol=new_packet.state_symbol if new_packet.state_symbol == other_pkt.state_symbol else None,
            dominant_cycle_stage=new_packet.cycle_stage if new_packet.cycle_stage == other_pkt.cycle_stage else None,
            dominant_identity_state=new_packet.identity_state if new_packet.identity_state == other_pkt.identity_state else None,
            summary=f"Convergence between {new_packet.agent_id} and {other_pkt.agent_id} in {new_packet.domain_id} (sim={semantic_sim:.2f})",
        )

        # Persist + update cooldown
        self.append_event(event)
        self._event_cooldowns[pair_key] = now_ts

        return event

    @staticmethod
    def _pair_key(agent_a: str, agent_b: str, domain_id: str) -> str:
        """Deterministic key for an agent pair + domain."""
        pair = tuple(sorted([agent_a, agent_b]))
        return f"{pair[0]}|{pair[1]}|{domain_id}"

    @staticmethod
    def _phase_alignment(a: ResonancePacket, b: ResonancePacket) -> float:
        """Score 0-1 for how aligned two packets' kernel phase states are."""
        score = 0.0
        # Cycle stage match (S0-S6)
        if a.cycle_stage and b.cycle_stage:
            if a.cycle_stage == b.cycle_stage:
                score += 0.6
            else:
                # Parse stage numbers for proximity
                try:
                    sa = int(a.cycle_stage.replace("S", "").replace("s", ""))
                    sb = int(b.cycle_stage.replace("S", "").replace("s", ""))
                    dist = abs(sa - sb)
                    if dist <= 1:
                        score += 0.3
                except (ValueError, AttributeError) as e:
                    log.debug("Stage number parse skipped: %s", e)
        # Identity state match
        if a.identity_state and b.identity_state:
            if a.identity_state == b.identity_state:
                score += 0.4
        return min(1.0, score)

    @staticmethod
    def _symbol_alignment(a: ResonancePacket, b: ResonancePacket) -> float:
        """Score 0-1 for symbol and loop_type overlap."""
        score = 0.0
        if a.state_symbol and b.state_symbol and a.state_symbol == b.state_symbol:
            score += 0.6
        if a.loop_type and b.loop_type and a.loop_type == b.loop_type:
            score += 0.4
        return min(1.0, score)

    @staticmethod
    def _motif_alignment(a: ResonancePacket, b: ResonancePacket) -> float:
        """Score 0-1 for motif overlap (Jaccard-like)."""
        if not a.motifs or not b.motifs:
            return 0.0
        set_a = set(a.motifs)
        set_b = set(b.motifs)
        union = set_a | set_b
        if not union:
            return 0.0
        return len(set_a & set_b) / len(union)

    @staticmethod
    def _shared_motifs(a: ResonancePacket, b: ResonancePacket) -> List[str]:
        """Return motifs shared between two packets."""
        if not a.motifs or not b.motifs:
            return []
        return sorted(set(a.motifs) & set(b.motifs))

    def _count_lines(self, path: str) -> int:
        """Count lines in a file without loading all data."""
        guarded_path = self._guard(path)
        if not os.path.exists(guarded_path):
            return 0
        count = 0
        with open(guarded_path, "r", encoding="utf-8") as f:
            for _ in f:
                count += 1
        return count
