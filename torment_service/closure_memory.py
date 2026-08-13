# torment_service/closure_memory.py
"""
Closure memory store for TORMENT — Block C, arc-closure synthesis.

Per docs/BLOCK_C_DESIGN.md §5.2 + §6.5. Stores end-of-arc closure
objects (what the arc was, what worked, what surprised, what to
carry forward, what remains open).

=== BOUNDARY RULE ===
Closure memory:
    - Stores whole arc-synthesis objects, NOT chunks or memories.
    - Is ethically load-bearing — closure is where "we're done with
      this arc" gets recorded as durable memory about the arc itself.
    - Is structurally separate from writeback at every layer:
        * distinct write_path (WRITE_CLOSURE_COMMIT)
        * distinct provenance factories (for_closure_{commit,ratification,revision})
        * distinct JSONL files (closures.jsonl, closure_events.jsonl)
        * distinct store (this module) and ledger (closure_ledger)
        * distinct test harness (tests/test_closure_*.py)
    - A closure commit is NOT a cognition writeback. Ratifier attribution
      is explicit; R+9 (no model-authored commits) is doctrine.

=== WATCH-ITEM HONORED LITERALLY ===
ONE `ClosureEntry` class. Lifecycle stages (proposed / ratified /
committed / revised) are NOT separate object ontologies — they are
event kinds in `ClosureLedger`. Raw event history remains literal;
trusted operational state is derived by the non-mutating reconciler.
No `ClosureProposal`, `RatifiedClosure`,
`CommittedClosure`, or `RevisedClosure` sibling classes exist.

=== R+8 HONORED LITERALLY ===
Revisions NEVER overwrite. Every `revise_closure` call produces a
NEW `version_id` alongside the prior version. The original remains
readable via `get_version(closure_id, original_version_id)`.
`version_history` grows on each revision; it does not replace.

=== R+10 HONORED LITERALLY ===
`deferred_or_open_items` is REQUIRED on every entry. Empty list is
accepted (v0.1 anti-false-finality, not full-truth-check). Absent /
`None` is rejected at the fabric layer before the entry is
constructed.
=== END BOUNDARY RULE ===
"""
from __future__ import annotations

import json
import logging
import os
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from .embedding_store import _canonical_storage_root, _child_path
from .pathing import safe_slug


log = logging.getLogger("torment.closure_memory")


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CLOSURE_MEMORY_CLASS = "closure"   # Never changes. Excluded from default lanes.


def _now_ts() -> int:
    return int(time.time())


# ---------------------------------------------------------------------------
# ClosureEntry — single class per watch-item (§12 handoff note 3)
# ---------------------------------------------------------------------------


@dataclass
class ClosureEntry:
    """One version of one closure.

    Lifecycle state is NOT stored on this entry. Raw lifecycle evidence lives
    in ClosureLedger; trusted operational state is derived by the
    non-mutating closure reconciliation helper.
    Adding a `state` / `is_committed` / `is_ratified` field here would
    violate the watch-item and the ratified design §5.4.

    `deferred_or_open_items` is REQUIRED — empty list is accepted, but
    the field must be present. The fabric layer rejects absence; this
    dataclass has no default for the field to keep that contract
    explicit at construction.
    """
    closure_id: str
    version_id: str
    workspace_id: str
    arc_name: str
    arc_kind: str
    scope: List[int]
    what_it_was: str
    what_worked: str
    what_surprised: str
    what_to_carry_forward: str
    deferred_or_open_items: List[str]          # REQUIRED — no default
    authorship_provenance: Dict[str, Any]      # ProvenanceV1.for_closure_commit dict
    version_history: List[Dict[str, Any]]      # empty on first version
    created_ts: int
    parent_version_id: Optional[str] = None    # set on revisions
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# ClosureStore — per-workspace persistence
# ---------------------------------------------------------------------------


class ClosureStore:
    """Per-workspace closure memory store.

    Each workspace owns a folder at `<data_dir>/workspaces/<ws>/closure_memory/`
    containing:

        closures.jsonl  - append-only; one line per ClosureEntry version.
                          Multiple versions of the same closure appear as
                          multiple lines. The store never overwrites — R+8.

        events.jsonl    - store-internal events (entry written, etc.).
                          The lifecycle ledger lives in a SEPARATE file
                          (`closure_events.jsonl`) owned by ClosureLedger,
                          per §7.3.

    Storage is NEVER shared with writeback audit paths, ArchiveStore,
    ReferenceStore, EnvironmentStore, or the ingest events file. Every
    pathing concern goes through `safe_slug` + `_canonical_storage_root`
    + `_guard` so a malformed workspace_id cannot escape.
    """

    def __init__(self, data_dir: str, workspace_id: str) -> None:
        self.workspace_id = safe_slug(workspace_id, "workspace_id")
        self.data_dir = _canonical_storage_root(data_dir)

        workspace_root = os.path.realpath(
            os.path.join(self.data_dir, "workspaces", self.workspace_id,
                         "closure_memory")
        )
        if not workspace_root.startswith(self.data_dir + os.sep):
            raise ValueError(
                f"Workspace closure-memory path escapes base: "
                f"{workspace_root!r}"
            )
        os.makedirs(workspace_root, exist_ok=True)
        self._base = workspace_root

        self.closures_path = _child_path(workspace_root, "closures.jsonl")
        self.events_path = _child_path(workspace_root, "events.jsonl")

        # In-memory index: closure_id -> List[ClosureEntry] (all versions,
        # in append order — oldest first).
        self._versions: Dict[str, List[ClosureEntry]] = {}
        self._load()

    # ------------------------------------------------------------------
    # Path safety
    # ------------------------------------------------------------------

    def _guard(self, path: str) -> str:
        rp = os.path.realpath(path)
        base = os.path.realpath(self._base)
        if rp != base and not rp.startswith(base + os.sep):
            raise ValueError(f"Path escapes workspace closure root: {rp!r}")
        return rp

    def _append_jsonl(self, path: str, obj: Dict[str, Any]) -> None:
        with open(self._guard(path), "a", encoding="utf-8") as f:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")

    def _load(self) -> None:
        """Load all versions from JSONL. Append order preserved."""
        if not os.path.exists(self.closures_path):
            return
        with open(self._guard(self.closures_path), "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                    entry = ClosureEntry(
                        closure_id=obj["closure_id"],
                        version_id=obj["version_id"],
                        workspace_id=obj["workspace_id"],
                        arc_name=obj["arc_name"],
                        arc_kind=obj["arc_kind"],
                        scope=list(obj.get("scope", [])),
                        what_it_was=obj.get("what_it_was", ""),
                        what_worked=obj.get("what_worked", ""),
                        what_surprised=obj.get("what_surprised", ""),
                        what_to_carry_forward=obj.get("what_to_carry_forward", ""),
                        deferred_or_open_items=list(
                            obj.get("deferred_or_open_items", [])
                        ),
                        authorship_provenance=obj.get("authorship_provenance", {}),
                        version_history=list(obj.get("version_history", [])),
                        created_ts=int(obj.get("created_ts", 0)),
                        parent_version_id=obj.get("parent_version_id"),
                        metadata=obj.get("metadata", {}),
                    )
                    self._versions.setdefault(entry.closure_id, []).append(entry)
                except (json.JSONDecodeError, KeyError):
                    continue

    # ------------------------------------------------------------------
    # Reads — all pure over the in-memory index
    # ------------------------------------------------------------------

    def get_version(
        self,
        closure_id: str,
        version_id: str,
    ) -> Optional[ClosureEntry]:
        """Return the specific (closure_id, version_id) pair, or None."""
        for entry in self._versions.get(closure_id, []):
            if entry.version_id == version_id:
                return entry
        return None

    def get_latest_version(self, closure_id: str) -> Optional[ClosureEntry]:
        """Return the most recently appended version of the closure, or None."""
        versions = self._versions.get(closure_id, [])
        if not versions:
            return None
        return versions[-1]

    def list_versions(self, closure_id: str) -> List[ClosureEntry]:
        """Return every version of the closure in append order (oldest first).

        R+8 guarantee: this list never shrinks — revisions append new
        entries; nothing is overwritten or removed.
        """
        return list(self._versions.get(closure_id, []))

    def list_closures(self) -> List[str]:
        """Return the set of closure_ids known to this store."""
        return list(self._versions.keys())

    # ------------------------------------------------------------------
    # Writes — append-only
    # ------------------------------------------------------------------

    def add_version(self, entry: ClosureEntry) -> None:
        """Append one closure version to the store.

        R+8: this is the ONLY write path. There is no update/overwrite/
        delete method. A "revision" is a new version_id appended here;
        the prior version remains in the JSONL and in the in-memory
        index forever.
        """
        self._versions.setdefault(entry.closure_id, []).append(entry)
        self._append_jsonl(self.closures_path, asdict(entry))
        self._append_jsonl(self.events_path, {
            "type": "CLOSURE_VERSION_WRITTEN",
            "ts": _now_ts(),
            "closure_id": entry.closure_id,
            "version_id": entry.version_id,
            "arc_name": entry.arc_name,
        })

    # ------------------------------------------------------------------
    # Id helpers — used by the fabric layer so id generation lives
    # next to the store rather than in the fabric's method bodies.
    # ------------------------------------------------------------------

    @staticmethod
    def new_closure_id() -> str:
        return f"closure_{uuid.uuid4().hex[:16]}"

    @staticmethod
    def new_version_id() -> str:
        return f"version_{uuid.uuid4().hex[:16]}"

    @property
    def closure_count(self) -> int:
        return len(self._versions)


# ---------------------------------------------------------------------------
# detect_open_items_mismatch — §8.1 concrete algorithm.
#
# Pure function over its inputs. Uses v0.1 signals only:
#   - ConflictRegistry.list(status="open") filtered to scope eids
#   - fabric.list_active_batons(...) filtered to scope eids
#
# Task residue is a NAMED GAP per D.5 — NOT checked here. Active
# reference loads are intentional reasoning material (not unresolved
# signals) and are NOT checked.
#
# Determinism: explicit yes/no on concrete signals; no fuzzy scoring,
# no "probably unresolved" heuristics, no confidence thresholding.
#
# Rigidity sniff test (§8.4): this is lifecycle-required-metadata
# enforcement, not truth-omniscience. Callers remain free to close the
# arc; they just must acknowledge what's unresolved. A non-empty
# declared_open_items satisfies the check even if it doesn't literally
# enumerate every unresolved item — anti-false-finality is the v0.1
# guard, not full-truth-check.
# ---------------------------------------------------------------------------


def detect_open_items_mismatch(
    fabric: Any,
    workspace_id: str,
    scope: List[int],
    declared_open_items: List[str],
) -> Dict[str, Any]:
    """Detect mismatch between known-unresolved signals in scope and
    declared open items.

    Signals (v0.1 — exhaustive for this check):
        1. ConflictRegistry.list(status="open") in every domain of the
           workspace, filtered to conflicts whose `eid_a` or `eid_b`
           is in `scope`.
        2. fabric.list_active_batons(...) across every agent in the
           workspace, filtered to active batons whose `eid` is in
           `scope`.

    Returns:
        {
            "mismatch": bool,
            "unresolved_conflicts": [
                {"conflict_id": str, "eid_a": int, "eid_b": int,
                 "domain_id": str}
            ],
            "unresolved_batons": [
                {"eid": int, "summary": str, "agent_id": str}
            ],
            "declared": [<copy of declared_open_items>],
            "reason": Optional[str],
        }

    Mismatch fires when:
        len(unresolved_conflicts) + len(unresolved_batons) > 0
        AND len(declared_open_items) == 0

    The narrower reading of this rule is deliberate — see §8.4 rigidity
    sniff test. The helper is NOT a generic closure-readiness engine;
    it only answers the specific question:

        "Does the closure claim no open items while known unresolved
        signals exist?"
    """
    scope_set = {int(e) for e in scope or []}
    declared = list(declared_open_items or [])

    unresolved_conflicts: List[Dict[str, Any]] = []
    unresolved_batons: List[Dict[str, Any]] = []

    # ---- Signal 1: ConflictRegistry open conflicts in scope ----
    #
    # Walk every domain's conflict registry for the workspace.
    # A conflict surfaces as "in scope" if EITHER eid_a or eid_b is
    # in the closure's scope — conflicts are symmetric pairs, and a
    # closure whose scope includes one side of a live conflict is
    # on the hook to acknowledge the dispute even if the other side
    # wasn't part of the arc.
    try:
        ws = fabric.get_workspace(workspace_id)
    except Exception:
        ws = None
    if ws is not None and hasattr(ws, "conflicts"):
        for domain_id, registry in ws.conflicts.items():
            try:
                opens = registry.list(status="open", limit=500)
            except Exception:
                continue
            for c in opens:
                eid_a = int(getattr(c, "eid_a", -1))
                eid_b = int(getattr(c, "eid_b", -1))
                if eid_a in scope_set or eid_b in scope_set:
                    unresolved_conflicts.append({
                        "conflict_id": getattr(c, "conflict_id", ""),
                        "eid_a": eid_a,
                        "eid_b": eid_b,
                        "domain_id": str(domain_id),
                    })

    # ---- Signal 2: Active batons in scope (across every agent) ----
    #
    # The baton payload is the authoritative lifecycle state.  The Fabric
    # helper reads persisted private graphs when needed, rather than treating
    # the lazy ``private_graphs`` runtime cache as the workspace agent index.
    active_batons = fabric._closure_active_batons(workspace_id)
    for baton in active_batons:
        try:
            eid = int(baton.get("eid", -1))
        except Exception:
            continue
        if eid in scope_set:
            unresolved_batons.append({
                "eid": eid,
                "summary": str(baton.get("summary", "")),
                "agent_id": str(baton.get("agent_id", "")),
            })

    has_unresolved = bool(unresolved_conflicts) or bool(unresolved_batons)
    deferred_empty = len(declared) == 0
    mismatch = has_unresolved and deferred_empty

    reason: Optional[str] = None
    if mismatch:
        parts = []
        if unresolved_conflicts:
            parts.append(
                f"{len(unresolved_conflicts)} open conflict(s) in scope"
            )
        if unresolved_batons:
            parts.append(
                f"{len(unresolved_batons)} active baton(s) in scope"
            )
        reason = (
            "declared_open_items is empty but "
            + " and ".join(parts)
            + " are present"
        )

    return {
        "mismatch": mismatch,
        "unresolved_conflicts": unresolved_conflicts,
        "unresolved_batons": unresolved_batons,
        "declared": declared,
        "reason": reason,
    }
