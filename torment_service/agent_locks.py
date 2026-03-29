# agent_locks.py — Per-agent serialization for concurrent safety
#
# TORMENT's in-memory state (agent_states, private_graphs, kernel state)
# is NOT thread-safe. Until internal atomic operations are added, ALL
# write operations targeting the same agent must be serialized.
#
# This module provides the locking infrastructure. The MCP layer or
# FastAPI middleware acquires the lock BEFORE calling any fabric method.
#
# Design:
#   - One RLock per (workspace_id, agent_id) pair
#   - Locks are created lazily (double-checked locking pattern)
#   - Workspace-level lock for shared state (collective field, proposals)
#   - Init lock for protecting lazy initialization of singletons
#
# Usage:
#   with lock_manager.agent_lock(workspace_id, agent_id):
#       fabric.ingest(...)
#
#   with lock_manager.workspace_lock(workspace_id):
#       fabric._get_collective_field(...)
# ---------------------------------------------------------------------------
from __future__ import annotations

import threading
from typing import Dict


class AgentLockManager:
    """Thread-safe lock manager for per-agent and per-workspace serialization.

    All locks are reentrant (RLock) so nested operations within the same
    thread don't deadlock.
    """

    def __init__(self) -> None:
        # Master lock protects the lock dictionaries themselves
        self._master = threading.Lock()
        self._agent_locks: Dict[str, threading.RLock] = {}
        self._workspace_locks: Dict[str, threading.RLock] = {}
        # Single init lock for lazy singleton creation (collective fields, etc.)
        self._init_lock = threading.RLock()

    @staticmethod
    def _agent_key(workspace_id: str, agent_id: str) -> str:
        return f"{workspace_id}/{agent_id}"

    def agent_lock(self, workspace_id: str, agent_id: str) -> threading.RLock:
        """Get or create an RLock for a specific agent.

        Returns the lock object — use it as a context manager:
            with lock_manager.agent_lock(ws, agent):
                ...
        """
        key = self._agent_key(workspace_id, agent_id)
        lock = self._agent_locks.get(key)
        if lock is not None:
            return lock
        # Double-checked locking
        with self._master:
            if key not in self._agent_locks:
                self._agent_locks[key] = threading.RLock()
            return self._agent_locks[key]

    def workspace_lock(self, workspace_id: str) -> threading.RLock:
        """Get or create an RLock for workspace-level shared state.

        Use for operations on collective fields, proposal bridges,
        shared graphs, and other workspace-scoped singletons.
        """
        lock = self._workspace_locks.get(workspace_id)
        if lock is not None:
            return lock
        with self._master:
            if workspace_id not in self._workspace_locks:
                self._workspace_locks[workspace_id] = threading.RLock()
            return self._workspace_locks[workspace_id]

    @property
    def init_lock(self) -> threading.RLock:
        """Lock for protecting lazy singleton initialization.

        Use for double-checked locking patterns:
            if key not in dict:
                with lock_manager.init_lock:
                    if key not in dict:
                        dict[key] = create_expensive_object()
        """
        return self._init_lock

    def cleanup_agent(self, workspace_id: str, agent_id: str) -> None:
        """Remove an agent lock (e.g. after agent deletion). Optional cleanup."""
        key = self._agent_key(workspace_id, agent_id)
        with self._master:
            self._agent_locks.pop(key, None)

    def stats(self) -> Dict[str, int]:
        """Return lock counts for diagnostics."""
        return {
            "agent_locks": len(self._agent_locks),
            "workspace_locks": len(self._workspace_locks),
        }
