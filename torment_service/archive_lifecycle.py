"""Append-only Archive document lifecycle replay."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional


DOCUMENT_INGESTED = "DOCUMENT_INGESTED"
DOCUMENT_DELETED = "DOCUMENT_DELETED"


@dataclass(frozen=True)
class CanonicalArchiveDocument:
    """The final persisted state for one Archive document ID.

    ``chunk_count`` is ``None`` when an older or malformed document record
    does not provide a usable boundary.  Callers retain the historical
    unbounded chunk behavior in that compatibility case.
    """

    record: Dict[str, Any]
    active: bool
    chunk_count: Optional[int]


def replay_document_lifecycle(events_path: str) -> Dict[str, bool]:
    """Return the final active state for each Archive document event.

    Events are processed in file order: an ingest activates a document and a
    deletion deactivates it. Documents absent from the returned mapping have
    no lifecycle event and remain active for legacy compatibility.
    """
    lifecycle: Dict[str, bool] = {}
    if not events_path or not os.path.exists(events_path):
        return lifecycle

    with open(events_path, "r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(event, dict):
                continue

            doc_id = event.get("doc_id")
            event_type = event.get("type")
            if not isinstance(doc_id, str) or not doc_id:
                continue
            if event_type == DOCUMENT_INGESTED:
                lifecycle[doc_id] = True
            elif event_type == DOCUMENT_DELETED:
                lifecycle[doc_id] = False

    return lifecycle


def _usable_chunk_count(record: Dict[str, Any]) -> Optional[int]:
    """Return a persisted chunk boundary, or ``None`` for legacy fallback."""
    if "chunk_count" not in record:
        return None
    try:
        chunk_count = int(record["chunk_count"])
    except (TypeError, ValueError):
        return None
    return chunk_count if chunk_count >= 0 else None


def replay_canonical_archive_documents(
    documents_path: str,
    events_path: str = "",
    *,
    legacy_deleted_fallback: bool = False,
) -> Dict[str, CanonicalArchiveDocument]:
    """Replay the canonical Archive document state from append-only JSONL.

    The last document record in file order is canonical for a ``doc_id``.
    Lifecycle events remain authoritative when present.  In the absence of an
    event, documents remain active for legacy compatibility; the compactor can
    additionally retain its historical ``_deleted`` fallback.
    """
    latest_by_id: Dict[str, Dict[str, Any]] = {}
    if documents_path and os.path.exists(documents_path):
        with open(documents_path, "r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(record, dict):
                    continue
                doc_id = record.get("doc_id")
                if isinstance(doc_id, str) and doc_id:
                    latest_by_id[doc_id] = record

    if not events_path and documents_path:
        events_path = os.path.join(
            os.path.dirname(os.path.realpath(documents_path)), "events.jsonl"
        )
    lifecycle = replay_document_lifecycle(events_path)

    canonical: Dict[str, CanonicalArchiveDocument] = {}
    for doc_id, record in latest_by_id.items():
        lifecycle_state = lifecycle.get(doc_id)
        active = (
            lifecycle_state
            if lifecycle_state is not None
            else not (legacy_deleted_fallback and record.get("_deleted", False))
        )
        canonical[doc_id] = CanonicalArchiveDocument(
            record=record,
            active=active,
            chunk_count=_usable_chunk_count(record),
        )
    return canonical


def is_current_archive_chunk(
    canonical_documents: Mapping[str, CanonicalArchiveDocument],
    doc_id: str,
    chunk_index: int,
) -> bool:
    """Whether a chunk belongs to the active canonical document incarnation.

    Current ArchiveStore writes always have a non-negative ``chunk_count`` and
    contiguous indexes.  Missing or malformed legacy ``chunk_count`` values
    intentionally retain their former unbounded behavior.
    """
    document = canonical_documents.get(doc_id)
    if document is None or not document.active:
        return False
    if document.chunk_count is None:
        return True
    return 0 <= chunk_index < document.chunk_count
