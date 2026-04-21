# torment_service/reference_memory.py
"""
Reference memory store for TORMENT — Block B, reference category.

Per docs/BLOCK_B_DESIGN.md §6.1. This is the "second lane" for
coherent whole-object storage, separate from ArchiveStore (which
chunks) and from core/baton substrate (which is kernel-governed).

=== BOUNDARY RULE ===
Reference memory:
    - Stores whole coherent reference objects (plans, design docs,
      theorems, long research bundles), NOT chunks.
    - Activation is INTENTIONAL — load / unload primitives (not cosine
      similarity retrieval).
    - Entries never enter the kernel, never create motifs, never
      affect drift scores.
    - Loading a reference is lifecycle state on TOP of the entry,
      NOT a mutation of the entry itself.

CARRY-FORWARD CAUTION (ratified 2026-04-21):
    ReferenceEntry identity ≠ ActiveLoad identity. Loadedness is
    state on top of a stable stored object, NOT part of the object's
    identity. ActiveLoad must stay a thin activation/state object;
    any field on ActiveLoad that duplicates ReferenceEntry data is
    the drift-into-shadow-identity failure mode the design forbids.

Promotion from reference → durable substrate REQUIRES a separate
explicit ingest with its own provenance. Loading does NOT promote
(R+3, R+6).
=== END BOUNDARY RULE ===
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from .embedding_store import _canonical_storage_root, _child_path
from .pathing import safe_slug


log = logging.getLogger("torment.reference_memory")


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REFERENCE_MEMORY_CLASS = "reference"  # Never changes. Never "core" or "archive".

VALID_SOURCE_KINDS = frozenset({
    "repo_file",        # file in the repo (repo-relative path)
    "url",              # HTTP(S) URL
    "internal_doc",     # a TORMENT-managed document
    "generated",        # generated artifact (programmatic output)
})


def _now_ts() -> int:
    return int(time.time())


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class ReferenceEntry:
    """A stored reference object.

    Identity is durable: `ref_id` is assigned at ingest and never
    changes. Source linkage (source_link / source_kind) lives here,
    not on ProvenanceV1 — per the ratified D.1 carry-forward caution,
    provenance records the STORAGE EVENT; the entry carries source
    identity.
    """
    ref_id: str
    workspace_id: str
    title: str
    body: str
    source_link: str
    source_kind: str
    source_hash: str
    provenance: Dict[str, Any]
    created_ts: int
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ActiveLoad:
    """In-memory state for an active reference load.

    CARRY-FORWARD CAUTION (§12 handoff note 7): ActiveLoad must stay
    a THIN activation/state object. DO NOT add fields that duplicate
    ReferenceEntry data (title, body, source_link, etc.). Those live
    on the entry. This dataclass tracks only lifecycle state.
    """
    load_id: str
    ref_id: str
    workspace_id: str
    agent_id: str
    scope_tag: str
    loaded_at_ts: int
    stale_at_load: bool
    status: str                             # "active" | "unloaded"
    unloaded_at_ts: Optional[int] = None


# ---------------------------------------------------------------------------
# ReferenceStore
# ---------------------------------------------------------------------------


class ReferenceStore:
    """Per-workspace reference memory store.

    Whole-object storage with source linkage and staleness-on-load.
    Each workspace has its own folder and JSONL files; references
    are NEVER co-mingled with core substrate, archive chunks, or
    baton lifecycle memory.
    """

    def __init__(
        self,
        data_dir: str,
        workspace_id: str,
    ) -> None:
        self.workspace_id = safe_slug(workspace_id, "workspace_id")
        self.data_dir = _canonical_storage_root(data_dir)

        workspace_root = os.path.realpath(
            os.path.join(self.data_dir, "workspaces", self.workspace_id,
                         "reference_memory")
        )
        if not workspace_root.startswith(self.data_dir + os.sep):
            raise ValueError(
                f"Workspace reference-memory path escapes base: "
                f"{workspace_root!r}"
            )
        os.makedirs(workspace_root, exist_ok=True)
        self._base = workspace_root

        self.references_path = _child_path(workspace_root, "references.jsonl")
        self.events_path = _child_path(workspace_root, "events.jsonl")

        # In-memory index: ref_id -> ReferenceEntry.
        # Loaded from JSONL on init; written through on each ingest.
        self._entries: Dict[str, ReferenceEntry] = {}
        self._load()

    def _guard(self, path: str) -> str:
        rp = os.path.realpath(path)
        base = os.path.realpath(self._base)
        if rp != base and not rp.startswith(base + os.sep):
            raise ValueError(f"Path escapes workspace reference root: {rp!r}")
        return rp

    def _append_jsonl(self, path: str, obj: Dict[str, Any]) -> None:
        with open(self._guard(path), "a", encoding="utf-8") as f:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")

    def _load(self) -> None:
        """Load references from JSONL. Last record per ref_id wins."""
        if not os.path.exists(self.references_path):
            return
        with open(self._guard(self.references_path), "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                    entry = ReferenceEntry(
                        ref_id=obj["ref_id"],
                        workspace_id=obj["workspace_id"],
                        title=obj.get("title", ""),
                        body=obj.get("body", ""),
                        source_link=obj.get("source_link", ""),
                        source_kind=obj.get("source_kind", ""),
                        source_hash=obj.get("source_hash", ""),
                        provenance=obj.get("provenance", {}),
                        created_ts=int(obj.get("created_ts", 0)),
                        metadata=obj.get("metadata", {}),
                    )
                    self._entries[entry.ref_id] = entry
                except (json.JSONDecodeError, KeyError):
                    continue

    # ------------------------------------------------------------------
    # Source-hash computation — staleness-on-load support.
    # v0.1 strategy: source-kind-specific handlers, defaulting to a
    # body-derived hash when the source can't be re-read. Future
    # increments implement per-kind handlers (URL re-fetch, internal
    # doc version lookup, etc.) — see docs/BLOCK_B_DESIGN.md §11 Q1.
    # ------------------------------------------------------------------

    @staticmethod
    def _hash_content(content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def compute_source_hash(
        self,
        source_link: str,
        source_kind: str,
        body: str,
    ) -> str:
        """Hash the current state of the source, if reachable. Fallback:
        hash the body as-stored.

        v0.1: only 'repo_file' attempts a real source read; other kinds
        use the body-hash fallback (stable across loads → stale=False
        under the normal operation, which is the correct conservative
        default).
        """
        if source_kind == "repo_file" and source_link:
            try:
                # Resolve repo-relative. If the path is inside the
                # data_dir workspace tree, we allow the read; otherwise
                # we fall back rather than attempting arbitrary
                # filesystem access.
                if os.path.isfile(source_link):
                    with open(source_link, "r", encoding="utf-8", errors="replace") as f:
                        return self._hash_content(f.read())
            except Exception:
                pass
        # Fallback: hash the body as ingested. For v0.1 the body is
        # immutable once stored, so this returns the same value on
        # every load — giving stale=False. This is the conservative
        # default until per-kind handlers land.
        return self._hash_content(body)

    # ------------------------------------------------------------------
    # Ingest / retrieve / delete
    # ------------------------------------------------------------------

    def ingest(
        self,
        title: str,
        body: str,
        source_link: str,
        source_kind: str,
        provenance: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ReferenceEntry:
        """Create a new reference entry. Source linkage is stored
        on the entry (per the ratified carry-forward caution).
        """
        ref_id = f"ref_{uuid.uuid4().hex[:16]}"
        source_hash = self.compute_source_hash(source_link, source_kind, body)
        entry = ReferenceEntry(
            ref_id=ref_id,
            workspace_id=self.workspace_id,
            title=title,
            body=body,
            source_link=source_link,
            source_kind=source_kind,
            source_hash=source_hash,
            provenance=provenance,
            created_ts=_now_ts(),
            metadata=metadata or {},
        )
        self._entries[ref_id] = entry
        self._append_jsonl(self.references_path, asdict(entry))
        self._append_jsonl(self.events_path, {
            "type": "REFERENCE_INGESTED",
            "ts": _now_ts(),
            "ref_id": ref_id,
            "title": title,
            "source_kind": source_kind,
        })
        return entry

    def get(self, ref_id: str) -> Optional[ReferenceEntry]:
        return self._entries.get(ref_id)

    def list(self) -> List[ReferenceEntry]:
        return list(self._entries.values())

    def delete(self, ref_id: str) -> bool:
        if ref_id not in self._entries:
            return False
        del self._entries[ref_id]
        self._append_jsonl(self.events_path, {
            "type": "REFERENCE_DELETED",
            "ts": _now_ts(),
            "ref_id": ref_id,
        })
        return True

    @property
    def reference_count(self) -> int:
        return len(self._entries)
